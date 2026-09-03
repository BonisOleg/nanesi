"""Thin views: parse → selector/service → render (ecommerce_business_logic_skill, rule 3)."""
from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from src.catalog.models import ProductVariant
from src.commerce import selectors, services
from src.commerce.forms import CheckoutForm
from src.commerce.models import Order
from src.commerce.models_1 import money
from src.commerce.payments.liqpay import get_liqpay_service
from src.content.models import SiteSettings
from src.core import analytics


def _saved_delivery_initial(user) -> dict:
    """Підставляє останні НП і Укрпошту; активний спосіб — той, що зберігали останнім заповненим."""
    initial = {}
    if user.saved_np_warehouse_name:
        initial["np_city_name"] = user.saved_np_city_name
        initial["np_city_ref"] = user.saved_np_city_ref
        initial["np_warehouse_name"] = user.saved_np_warehouse_name
        initial["np_warehouse_ref"] = user.saved_np_warehouse_ref
        initial["delivery_method"] = Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE
    if user.saved_ukrposhta_address or user.saved_ukrposhta_index:
        initial["ukrposhta_index"] = user.saved_ukrposhta_index
        initial["ukrposhta_address"] = user.saved_ukrposhta_address
        if not user.saved_np_warehouse_name:
            initial["delivery_method"] = Order.DeliveryMethod.UKRPOSHTA
    return initial


def _cart_context(request):
    cart = selectors.get_cart(request)
    lines = selectors.cart_lines(cart)
    subtotal = money(selectors.cart_subtotal(lines))
    discount_amount = None
    if cart and cart.promo_code_id:
        is_valid, _message = cart.promo_code.is_valid_now(subtotal=subtotal)
        discount_amount = cart.promo_code.calculate_discount(subtotal) if is_valid else None
    # Поріг безкоштовної доставки — від суми товарів ДО промокоду (п.9 UX).
    progress = selectors.free_shipping_progress(subtotal)
    cart_items_count = sum(line.qty for line in lines)
    return {
        "cart": cart,
        "lines": lines,
        "subtotal": subtotal,
        "shipping_progress": progress,
        "promo_code": cart.promo_code if cart else None,
        "discount_amount": discount_amount,
        "total": money(subtotal - (discount_amount or 0)),
        "cart_items_count": cart_items_count,
    }


class CartView(View):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        # Кожен інший шаблон (каталог/картка товару) лінкує сюди «Додати в кошик»,
        # тому CSRF-кука має бути видана незалежно від того, чи кошик наразі порожній.
        context = analytics.attach_pending_events(_cart_context(request), request)
        return render(request, "commerce/cart.html", context)


@ensure_csrf_cookie
@require_GET
def cart_summary_fragment(request):
    """Фрагмент для drawer/popup кошика (HTMX / fetch)."""
    context = analytics.attach_pending_events(_cart_context(request), request)
    context["in_drawer"] = True
    return render(request, "commerce/partials/cart_summary.html", context)


def _wants_json(request) -> bool:
    accept = request.headers.get("Accept") or ""
    return (
        request.headers.get("X-Requested-With") == "fetch"
        or "application/json" in accept
        or request.POST.get("ajax") == "1"
    )


def _cart_qty_total(cart) -> int:
    return sum(cart.items.values_list("qty", flat=True))


@require_POST
def cart_add(request, variant_id: int):
    qty = int(request.POST.get("qty") or 1)
    cart = None
    product_id = None
    try:
        cart = services.add_item(request, variant_id, qty=qty)
        variant = ProductVariant.objects.select_related("product__brand", "product__category").filter(pk=variant_id).first()
        if variant:
            product_id = variant.product_id
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
        if _wants_json(request):
            return JsonResponse({"ok": False, "error": str(exc)}, status=400)
        messages.error(request, str(exc))
    if _wants_json(request):
        count = _cart_qty_total(cart) if cart is not None else 0
        return JsonResponse({
            "ok": True,
            "count": count,
            "variant_id": variant_id,
            "product_id": product_id,
        })
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
    is_hx = bool(request.headers.get("HX-Request"))
    promo_feedback = None
    try:
        services.apply_promo_code(request, code)
        if not is_hx:
            messages.success(request, _("Промокод застосовано"))
    except services.PromoError as exc:
        if is_hx:
            promo_feedback = str(exc)
        else:
            messages.error(request, str(exc))
    if is_hx:
        context = _cart_context(request)
        if promo_feedback:
            context["promo_feedback"] = promo_feedback
            context["promo_feedback_level"] = "error"
        return render(request, "commerce/partials/cart_summary.html", context)
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
        cart = context["cart"]
        initial = {
            "full_name": request.user.get_full_name() if request.user.is_authenticated else "",
            "email": request.user.email if request.user.is_authenticated else "",
            "phone": request.user.phone if request.user.is_authenticated else "",
        }
        if cart:
            # Контакти з попередньої спроби checkout (покинутий кошик) — фолбек для гостя
            # і доповнення порожніх полів у авторизованого.
            if not initial["full_name"]:
                initial["full_name"] = cart.contact_full_name
            if not initial["phone"]:
                initial["phone"] = cart.contact_phone
            if not initial["email"]:
                initial["email"] = cart.contact_email
        if request.user.is_authenticated:
            initial.update(_saved_delivery_initial(request.user))
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
        # Гачок під покинутий кошик: контакти пишемо одразу, навіть якщо форма з помилками.
        services.save_cart_contacts(
            request,
            full_name=request.POST.get("full_name", ""),
            phone=request.POST.get("phone", ""),
            email=request.POST.get("email", ""),
        )
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
        return render(request, "commerce/thank_you.html", self._context(request, order))

    def post(self, request, order_number: str):
        order = selectors.get_order_for_thanks(request, order_number)
        if order is None:
            messages.error(request, _("Замовлення не знайдено"))
            return redirect("commerce:cart")

        if request.POST.get("action") == "change_payment":
            try:
                services.change_unpaid_card_payment_method(
                    order, request.POST.get("payment_method", ""),
                )
                messages.success(request, _("Спосіб оплати змінено"))
            except services.PaymentMethodError as exc:
                messages.error(request, str(exc))
            order.refresh_from_db()

        return redirect("commerce:thank_you", order_number=order.number)

    def _context(self, request, order: Order) -> dict:
        # purchase — після створення замовлення (не після успішної оплати карткою)
        dl_events_json = analytics.events_json(analytics.build_event(
            "purchase",
            value=order.total,
            items=[
                analytics.make_item(
                    item_id=item.sku,
                    item_name=item.product_name,
                    price=item.unit_price,
                    quantity=item.qty,
                )
                for item in order.items.all()
            ],
            extra={
                "transaction_id": order.number,
                "shipping": float(order.shipping_cost) if order.shipping_cost else 0,
                "coupon": order.promo_code_snapshot or None,
            },
        ))
        site = SiteSettings.load()
        show_payment_pending = (
            order.payment_method == Order.PaymentMethod.CARD_ONLINE
            and order.payment_status == Order.PaymentStatus.UNPAID
        )
        context = {
            "order": order,
            "dl_events_json": dl_events_json,
            "thank_you_title": site.thank_you_title_display(),
            "thank_you_number_label": site.thank_you_number_label_display(),
            "thank_you_body": site.thank_you_body_display(order.phone),
            "show_bank_requisites": False,
            "show_payment_pending": show_payment_pending,
            "payment_pending_title": site.payment_pending_title_display(),
            "payment_pending_body": site.payment_pending_body_display(),
            "can_retry_payment": show_payment_pending and get_liqpay_service() is not None,
            "alternate_payment_methods": (
                selectors.alternate_payment_methods_after_card() if show_payment_pending else []
            ),
        }
        if order.payment_method == Order.PaymentMethod.BANK_TRANSFER:
            requisites = site.bank_requisites_for_display()
            if requisites:
                context.update(requisites)
                context["show_bank_requisites"] = True
        return context


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
