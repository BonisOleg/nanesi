"""Thin views: parse → selector/service → render (ecommerce_business_logic_skill, rule 3)."""
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from src.catalog.models import ProductVariant
from src.commerce import selectors, services
from src.commerce.forms import CheckoutForm
from src.commerce.models import Order
from src.commerce.payments.liqpay import get_liqpay_service
from src.core import analytics


def _cart_context(request):
    cart = selectors.get_cart(request)
    lines = selectors.cart_lines(cart)
    subtotal = selectors.cart_subtotal(lines)
    progress = selectors.free_shipping_progress(subtotal)
    discount_amount = None
    if cart and cart.promo_code_id:
        is_valid, message = cart.promo_code.is_valid_now(subtotal=subtotal)
        discount_amount = cart.promo_code.calculate_discount(subtotal) if is_valid else None
    return {
        "cart": cart,
        "lines": lines,
        "subtotal": subtotal,
        "shipping_progress": progress,
        "promo_code": cart.promo_code if cart else None,
        "discount_amount": discount_amount,
        "total": subtotal - (discount_amount or 0),
    }


class CartView(View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        # Кожен інший шаблон (каталог/картка товару) лінкує сюди «Додати в кошик»,
        # тому CSRF-кука має бути видана незалежно від того, чи кошик наразі порожній.
        context = analytics.attach_pending_events(_cart_context(request), request)
        return render(request, "commerce/cart.html", context)


@require_POST
def cart_add(request, variant_id: int):
    qty = int(request.POST.get("qty") or 1)
    try:
        services.add_item(request, variant_id, qty=qty)
        variant = ProductVariant.objects.select_related("product__brand", "product__category").filter(pk=variant_id).first()
        if variant:
            analytics.queue_event(request, analytics.build_event(
                "add_to_cart",
                value=variant.current_price * qty,
                items=[analytics.make_item(
                    item_id=variant.sku, item_name=variant.product.name,
                    price=variant.current_price, quantity=qty,
                    brand=variant.product.brand.name, category=variant.product.category.name,
                )],
            ))
    except services.CartError as exc:
        messages.error(request, str(exc))
    if request.headers.get("HX-Request"):
        context = analytics.attach_pending_events(_cart_context(request), request)
        return render(request, "commerce/partials/cart_summary.html", context)
    return redirect("commerce:cart")


@require_POST
def cart_update(request, item_id: int):
    try:
        services.update_item_qty(request, item_id, qty=int(request.POST.get("qty") or 0))
    except services.CartError as exc:
        messages.error(request, str(exc))
    if request.headers.get("HX-Request"):
        return render(request, "commerce/partials/cart_summary.html", _cart_context(request))
    return redirect("commerce:cart")


@require_POST
def cart_remove(request, item_id: int):
    services.remove_item(request, item_id)
    if request.headers.get("HX-Request"):
        return render(request, "commerce/partials/cart_summary.html", _cart_context(request))
    return redirect("commerce:cart")


@require_POST
def promo_apply(request):
    code = request.POST.get("code", "")
    try:
        services.apply_promo_code(request, code)
        messages.success(request, _("Промокод застосовано"))
    except services.PromoError as exc:
        messages.error(request, str(exc))
    if request.headers.get("HX-Request"):
        return render(request, "commerce/partials/cart_summary.html", _cart_context(request))
    return redirect("commerce:cart")


@require_POST
def promo_remove(request):
    services.remove_promo_code(request)
    if request.headers.get("HX-Request"):
        return render(request, "commerce/partials/cart_summary.html", _cart_context(request))
    return redirect("commerce:cart")


class CheckoutView(View):
    def get(self, request):
        context = _cart_context(request)
        if not context["lines"]:
            messages.info(request, _("Кошик порожній"))
            return redirect("commerce:cart")
        initial = {
            "full_name": request.user.get_full_name() if request.user.is_authenticated else "",
            "email": request.user.email if request.user.is_authenticated else "",
            "phone": request.user.phone if request.user.is_authenticated else "",
        }
        if request.user.is_authenticated and request.user.saved_np_warehouse_name:
            initial["delivery_method"] = Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE
            initial["np_city_name"] = request.user.saved_np_city_name
            initial["np_city_ref"] = request.user.saved_np_city_ref
            initial["np_warehouse_name"] = request.user.saved_np_warehouse_name
            initial["np_warehouse_ref"] = request.user.saved_np_warehouse_ref
        context["form"] = CheckoutForm(initial=initial)
        context["dl_events_json"] = analytics.events_json(analytics.build_event(
            "begin_checkout",
            value=context["total"],
            items=[
                analytics.make_item(item_id=line.sku, item_name=line.name, price=line.unit_price, quantity=line.qty)
                for line in context["lines"]
            ],
        ))
        return render(request, "commerce/checkout.html", context)

    def post(self, request):
        form = CheckoutForm(request.POST)
        context = _cart_context(request)
        if not context["lines"]:
            messages.info(request, _("Кошик порожній"))
            return redirect("commerce:cart")
        if not form.is_valid():
            context["form"] = form
            return render(request, "commerce/checkout.html", context)
        try:
            order = services.place_order(request, form.cleaned_data)
        except services.CartError as exc:
            messages.error(request, str(exc))
            context["form"] = form
            return render(request, "commerce/checkout.html", context)

        if order.payment_method == Order.PaymentMethod.CARD_ONLINE:
            return redirect("commerce:payment_init", order_number=order.number)
        return redirect("commerce:thank_you", order_number=order.number)


class ThankYouView(View):
    def get(self, request, order_number: str):
        order = selectors.get_order_for_thanks(request, order_number)
        if order is None:
            messages.error(request, _("Замовлення не знайдено"))
            return redirect("commerce:cart")
        dl_events_json = analytics.events_json(analytics.build_event(
            "purchase",
            value=order.total,
            items=[
                analytics.make_item(item_id=item.sku, item_name=item.product_name, price=item.unit_price, quantity=item.qty)
                for item in order.items.all()
            ],
            extra={
                "transaction_id": order.number,
                "shipping": float(order.shipping_cost) if order.shipping_cost else 0,
                "coupon": order.promo_code_snapshot or None,
            },
        ))
        return render(request, "commerce/thank_you.html", {"order": order, "dl_events_json": dl_events_json})


class PaymentInitView(View):
    """Гість-безпечно: доступ лише за номером зі session['last_order_number'] (SEC-01)."""

    def get(self, request, order_number: str):
        order = selectors.get_order_for_thanks(request, order_number)
        if order is None:
            messages.error(request, _("Замовлення не знайдено"))
            return redirect("commerce:cart")

        liqpay = get_liqpay_service()
        if liqpay is None:
            messages.warning(request, _("Оплата карткою тимчасово недоступна — оберіть інший спосіб або зверніться до нас"))
            return redirect("commerce:thank_you", order_number=order.number)

        result_url = request.build_absolute_uri(reverse("commerce:payment_callback", kwargs={"order_number": order.number}))
        checkout_data = liqpay.create_checkout_data(
            order_number=order.number,
            amount=float(order.total),
            description=f"Замовлення №{order.number}",
            result_url=result_url,
            server_url=settings.LIQPAY_SERVER_URL,
        )
        return render(request, "commerce/payment_init.html", {"order": order, "checkout": checkout_data})


@csrf_exempt
@require_POST
def payment_webhook(request):
    """SEC-07: єдине джерело істини для статусу оплати — підписаний server callback."""
    liqpay = get_liqpay_service()
    if liqpay is None:
        return HttpResponse("LiqPay not configured", status=503)

    data_b64 = request.POST.get("data", "")
    signature = request.POST.get("signature", "")
    if not data_b64 or not signature or not liqpay.verify_callback(data_b64, signature):
        return HttpResponse("Invalid signature", status=403)

    payload = liqpay.decode_data(data_b64)
    order_number = payload.get("order_id", "")
    status = payload.get("status", "")
    payment_id = str(payload.get("payment_id", ""))
    if not order_number:
        return HttpResponse("Missing order_id", status=400)

    with transaction.atomic():
        order = Order.objects.select_for_update().filter(number=order_number).first()
        if order is None:
            return HttpResponse("Order not found", status=404)

        idem_key = f"liqpay_{payment_id}_{status}"
        if order.payment_idempotency_key == idem_key:
            return HttpResponse("OK (idempotent)", status=200)

        if status in ("success", "sandbox"):
            order.payment_status = Order.PaymentStatus.PAID
            order.payment_intent_id = payment_id
            order.payment_idempotency_key = idem_key
            order.paid_at = timezone.now()
            order.save()
            try:
                services.change_order_status(order, Order.Status.PAID)
            except services.OrderStatusError:
                pass
        elif status in ("failure", "error", "reversed"):
            order.payment_idempotency_key = idem_key
            order.save(update_fields=["payment_idempotency_key", "updated_at"])

    return HttpResponse("OK", status=200)


@csrf_exempt
def payment_callback(request, order_number: str):
    """result_url — лише UX-редирект, статус нею НЕ встановлюється (SEC-07)."""
    order = get_object_or_404(Order, number=order_number)
    return redirect("commerce:thank_you", order_number=order.number)
