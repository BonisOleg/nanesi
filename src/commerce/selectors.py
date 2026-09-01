"""Тільки читання (ecommerce_business_logic_skill, шар selectors). Ціна — завжди
жива з ProductVariant, ніколи з кешу кошика (SEC-02/06)."""
from dataclasses import dataclass
from decimal import Decimal

from src.commerce.models import Cart, Order
from src.content.models import SiteSettings


def get_cart(request) -> Cart | None:
    """Лише пошук — без створення (створення це мутація, services.get_or_create_cart)."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user, status=Cart.Status.OPEN).first()
        if cart:
            return cart
    session_key = request.session.session_key
    if not session_key:
        return None
    return Cart.objects.filter(session_key=session_key, status=Cart.Status.OPEN).first()


@dataclass
class CartLine:
    item_id: int
    variant_id: int
    name: str
    sku: str
    shade: str
    volume: str
    unit_price: Decimal
    qty: int
    line_total: Decimal
    in_stock: bool
    stock_quantity: int


def cart_lines(cart: Cart | None) -> list[CartLine]:
    if cart is None:
        return []
    lines = []
    items = cart.items.select_related("product_variant", "product_variant__product").order_by("added_at")
    for item in items:
        variant = item.product_variant
        unit_price = variant.current_price
        lines.append(CartLine(
            item_id=item.pk,
            variant_id=variant.pk,
            name=variant.product.name,
            sku=variant.sku,
            shade=variant.shade,
            volume=variant.volume,
            unit_price=unit_price,
            qty=item.qty,
            line_total=unit_price * item.qty,
            in_stock=variant.in_stock,
            stock_quantity=variant.stock_quantity,
        ))
    return lines


def cart_subtotal(lines: list[CartLine]) -> Decimal:
    return sum((line.line_total for line in lines), Decimal("0"))


@dataclass
class FreeShippingProgress:
    threshold: Decimal | None
    remaining: Decimal
    reached: bool


def free_shipping_progress(subtotal: Decimal) -> FreeShippingProgress:
    threshold = SiteSettings.load().free_shipping_threshold
    if not threshold:
        return FreeShippingProgress(threshold=None, remaining=Decimal("0"), reached=False)
    remaining = max(Decimal("0"), threshold - subtotal)
    return FreeShippingProgress(threshold=threshold, remaining=remaining, reached=subtotal >= threshold)


def available_delivery_methods() -> list[tuple[str, str]]:
    settings_obj = SiteSettings.load()
    methods = []
    if settings_obj.nova_poshta_enabled:
        methods.append((Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE, Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE.label))
        methods.append((Order.DeliveryMethod.NOVA_POSHTA_COURIER, Order.DeliveryMethod.NOVA_POSHTA_COURIER.label))
    if settings_obj.ukrposhta_enabled:
        methods.append((Order.DeliveryMethod.UKRPOSHTA, Order.DeliveryMethod.UKRPOSHTA.label))
    return methods


def available_payment_methods() -> list[tuple[str, str]]:
    from django.conf import settings as dj_settings

    settings_obj = SiteSettings.load()
    methods = []
    if settings_obj.card_payment_enabled and dj_settings.LIQPAY_PUBLIC_KEY:
        methods.append((Order.PaymentMethod.CARD_ONLINE, Order.PaymentMethod.CARD_ONLINE.label))
    if settings_obj.cash_on_delivery_enabled:
        methods.append((Order.PaymentMethod.CASH_ON_DELIVERY, Order.PaymentMethod.CASH_ON_DELIVERY.label))
    if settings_obj.bank_transfer_enabled:
        methods.append((Order.PaymentMethod.BANK_TRANSFER, Order.PaymentMethod.BANK_TRANSFER.label))
    return methods


def my_orders(user):
    """SEC-01: замовлення лише власника."""
    return Order.objects.filter(user=user).order_by("-created_at")


def get_order_for_thanks(request, order_number: str) -> Order | None:
    """Гість-thanks: доступ лише якщо номер збігається з session['last_order_number']
    (SEC-01, гостьовий варіант) — не голий pk із query-параметра."""
    last_number = request.session.get("last_order_number")
    if last_number and last_number == order_number:
        return Order.objects.filter(number=order_number).first()
    if request.user.is_authenticated:
        return Order.objects.filter(number=order_number, user=request.user).first()
    return None
