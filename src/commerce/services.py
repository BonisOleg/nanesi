"""Мутації — транзакційно, власні винятки (ecommerce_business_logic_skill, шар services).

SEC-02/06: ціна ніколи не приймається з форми/кошика — рахується з `ProductVariant`
у момент виклику. SEC-03: лічильник промокоду — `select_for_update()`. ERR-BIZ-05:
залишок склад — `F()`-update з умовою, не read-then-write.
"""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils.translation import gettext as _

from src.accounts.permissions import user_can_manage_orders
from src.catalog.models import ProductVariant
from src.commerce.integrations import queue_order_event
from src.commerce.models import Cart, CartItem, Order, OrderIntegrationEvent, OrderItem, OrderStatusLog, PromoCode
from src.commerce.selectors import cart_lines, cart_subtotal

logger = logging.getLogger(__name__)


class CartError(Exception):
    pass


class PromoError(Exception):
    pass


class OrderError(Exception):
    pass


class OrderStatusError(Exception):
    pass


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Order.Status.NEW: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
    Order.Status.CONFIRMED: {Order.Status.PAID, Order.Status.ASSEMBLING, Order.Status.CANCELLED},
    Order.Status.PAID: {Order.Status.ASSEMBLING, Order.Status.CANCELLED},
    Order.Status.ASSEMBLING: {Order.Status.SHIPPED, Order.Status.CANCELLED},
    Order.Status.SHIPPED: {Order.Status.DELIVERED},
    Order.Status.DELIVERED: set(),
    Order.Status.CANCELLED: set(),
}


def _ensure_session(request) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def get_or_create_cart(request) -> Cart:
    if request.user.is_authenticated:
        cart, _created = Cart.objects.get_or_create(user=request.user, status=Cart.Status.OPEN)
        return cart
    session_key = _ensure_session(request)
    cart, _created = Cart.objects.get_or_create(session_key=session_key, status=Cart.Status.OPEN)
    return cart


@transaction.atomic
def add_item(request, variant_id: int, qty: int = 1) -> Cart:
    variant = ProductVariant.objects.filter(pk=variant_id, is_active=True).select_related("product").first()
    if variant is None:
        raise CartError(_("Товар не знайдено"))
    if not variant.in_stock:
        raise CartError(_("Товару немає в наявності"))

    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product_variant=variant, defaults={"qty": 0})
    new_qty = item.qty + max(1, int(qty))
    item.qty = min(new_qty, variant.stock_quantity)
    item.save(update_fields=["qty"])
    cart.save(update_fields=["updated_at"])
    return cart


@transaction.atomic
def update_item_qty(request, item_id: int, qty: int) -> Cart:
    cart = get_or_create_cart(request)
    item = cart.items.select_related("product_variant").filter(pk=item_id).first()
    if item is None:
        raise CartError(_("Товар у кошику не знайдено"))
    qty = int(qty)
    if qty <= 0:
        item.delete()
    else:
        item.qty = min(qty, item.product_variant.stock_quantity or qty)
        item.save(update_fields=["qty"])
    cart.save(update_fields=["updated_at"])
    return cart


@transaction.atomic
def remove_item(request, item_id: int) -> Cart:
    cart = get_or_create_cart(request)
    cart.items.filter(pk=item_id).delete()
    cart.save(update_fields=["updated_at"])
    return cart


@transaction.atomic
def apply_promo_code(request, code: str) -> PromoCode:
    cart = get_or_create_cart(request)
    subtotal = cart_subtotal(cart_lines(cart))
    promo = PromoCode.objects.select_for_update().filter(code=code.strip().upper()).first()
    if promo is None:
        raise PromoError(_("Промокод не знайдено"))
    is_valid, message = promo.is_valid_now(subtotal=subtotal)
    if not is_valid:
        raise PromoError(message)
    cart.promo_code = promo
    cart.save(update_fields=["promo_code", "updated_at"])
    return promo


@transaction.atomic
def remove_promo_code(request) -> Cart:
    cart = get_or_create_cart(request)
    cart.promo_code = None
    cart.save(update_fields=["promo_code", "updated_at"])
    return cart


@transaction.atomic
def place_order(request, cleaned_data: dict) -> Order:
    """Гість-checkout (Відповіді п.6): user nullable. Ревалідація ціни/залишку —
    завжди з БД (SEC-02), незалежно від того, що показувалось у кошику раніше."""
    cart = get_or_create_cart(request)
    items = list(
        cart.items.select_for_update().select_related("product_variant", "product_variant__product"),
    )
    if not items:
        raise CartError(_("Кошик порожній"))

    for item in items:
        variant = item.product_variant
        if not variant.is_active or item.qty > variant.stock_quantity:
            raise CartError(
                _("«%(name)s» (%(sku)s) — недостатньо на складі (в наявності %(stock)s, у кошику %(qty)s)")
                % {
                    "name": variant.product.name, "sku": variant.sku,
                    "stock": variant.stock_quantity, "qty": item.qty,
                },
            )

    subtotal = sum((item.product_variant.current_price * item.qty for item in items), Decimal("0"))

    discount_amount = Decimal("0")
    promo = None
    if cart.promo_code_id:
        promo = PromoCode.objects.select_for_update().filter(pk=cart.promo_code_id).first()
        if promo:
            is_valid, _message = promo.is_valid_now(subtotal=subtotal)
            if is_valid:
                discount_amount = promo.calculate_discount(subtotal)
            else:
                promo = None  # промокод став невалідним між кошиком і checkout — тихо ігноруємо, не блокуємо замовлення

    shipping_cost = None
    from src.content.models import SiteSettings

    threshold = SiteSettings.load().free_shipping_threshold
    if threshold and (subtotal - discount_amount) >= threshold:
        shipping_cost = Decimal("0")

    total = subtotal - discount_amount + (shipping_cost or Decimal("0"))

    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        full_name=cleaned_data["full_name"],
        phone=cleaned_data["phone"],
        email=cleaned_data.get("email", ""),
        delivery_method=cleaned_data["delivery_method"],
        np_city_name=cleaned_data.get("np_city_name", ""),
        np_city_ref=cleaned_data.get("np_city_ref", ""),
        np_warehouse_name=cleaned_data.get("np_warehouse_name", ""),
        np_warehouse_ref=cleaned_data.get("np_warehouse_ref", ""),
        ukrposhta_address=cleaned_data.get("ukrposhta_address", ""),
        payment_method=cleaned_data["payment_method"],
        subtotal=subtotal,
        discount_amount=discount_amount,
        shipping_cost=shipping_cost,
        total=total,
        promo_code=promo,
        promo_code_snapshot=promo.code if promo else "",
        comment=cleaned_data.get("comment", ""),
    )
    OrderStatusLog.objects.create(order=order, from_status="", to_status=order.status)

    for item in items:
        variant = item.product_variant
        OrderItem.objects.create(
            order=order,
            product_variant=variant,
            product_name=variant.product.name,
            sku=variant.sku,
            unit_price=variant.current_price,
            qty=item.qty,
            line_total=variant.current_price * item.qty,
        )
        updated = ProductVariant.objects.filter(pk=variant.pk, stock_quantity__gte=item.qty).update(
            stock_quantity=F("stock_quantity") - item.qty,
        )
        if not updated:
            raise CartError(_("«%(name)s» щойно розкупили — оформіть замовлення ще раз") % {"name": variant.product.name})

    if promo:
        PromoCode.objects.filter(pk=promo.pk).update(used_count=F("used_count") + 1)

    cart.items.all().delete()
    cart.status = Cart.Status.CONVERTED
    cart.promo_code = None
    cart.save(update_fields=["status", "promo_code", "updated_at"])

    request.session["last_order_number"] = order.number
    queue_order_event(order, OrderIntegrationEvent.EventType.ORDER_CREATED)
    return order


@transaction.atomic
def change_order_status(order: Order, to_status: str, *, user=None, note: str = "") -> Order:
    if user is not None and not user_can_manage_orders(user):
        raise OrderStatusError("Немає права змінювати статус замовлення")
    if to_status not in ALLOWED_TRANSITIONS.get(order.status, set()):
        raise OrderStatusError(f"Перехід {order.status} → {to_status} заборонено")

    from_status = order.status
    order.status = to_status
    if to_status == Order.Status.PAID:
        from django.utils import timezone

        order.payment_status = Order.PaymentStatus.PAID
        order.paid_at = timezone.now()
    order.save()
    OrderStatusLog.objects.create(order=order, from_status=from_status, to_status=to_status, note=note, changed_by=user)
    queue_order_event(
        order, OrderIntegrationEvent.EventType.STATUS_CHANGED,
        extra={"from_status": from_status, "to_status": to_status},
    )

    if to_status in (Order.Status.PAID, Order.Status.ASSEMBLING):
        from src.shipping.services import dispatch_shipment_for_order

        dispatch_shipment_for_order(order.pk)

    return order
