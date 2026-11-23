"""Thin views: parse → selector/service → render (ecommerce_business_logic_skill, rule 3)."""
import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from src.catalog.models import ProductVariant
from src.commerce import selectors, services
from src.commerce.forms import CheckoutForm
from src.commerce.models import Order
from src.commerce.models_1 import money
from src.commerce.payments.monobank import MonobankError, get_monobank_service
from src.commerce.views_1 import payment_callback, payment_webhook, salesdrive_webhook
from src.content.models import SiteSettings
from src.core import analytics
from src.core.ratelimit import ratelimit

logger = logging.getLogger(__name__)


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
    checkout_blocked = any(
        (not line.in_stock) or line.qty > line.stock_quantity
        for line in lines
    )
    return {
        "cart": cart,
        "lines": lines,
        "subtotal": subtotal,
        "shipping_progress": progress,
        "promo_code": cart.promo_code if cart else None,
        "discount_amount": discount_amount,
        "total": money(subtotal - (discount_amount or 0)),
        "cart_items_count": cart_items_count,
        "checkout_blocked": checkout_blocked,
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


def _parse_qty(raw, default: int = 1) -> int | None:
    if raw in (None, ""):
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _invalid_qty_response(request):
    message = _("Некоректна кількість")
    if _wants_json(request):
        return JsonResponse({"ok": False, "error": str(message)}, status=400)
    messages.error(request, message)
    return redirect("commerce:cart")


@require_POST
def cart_add(request, variant_id: int):
    qty = _parse_qty(request.POST.get("qty"), default=1)
    if qty is None:
        return _invalid_qty_response(request)
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
    qty = _parse_qty(request.POST.get("qty"), default=0)
    if qty is None:
        return _invalid_qty_response(request)
    try:
        services.update_item_qty(request, item_id, qty=qty)
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
@ratelimit(scope="promo", limit=10, window=300)
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


@method_decorator(ratelimit(scope="checkout", limit=40, window=300), name="post")
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
        form = CheckoutForm(request.POST)
        context = _cart_context(request)
        if not context["lines"]:
            messages.info(request, _("Кошик порожній"))
            return redirect("commerce:cart")
        if form.honeypot_triggered():
            context["form"] = CheckoutForm()
            return render(request, "commerce/checkout.html", context)
        # Гачок під покинутий кошик: лише валідні контакти, навіть якщо форма з помилками.
        services.save_cart_contacts(
            request,
            full_name=request.POST.get("full_name", ""),
            phone=request.POST.get("phone", ""),
            email=request.POST.get("email", ""),
        )
        if not form.is_valid():
            context["form"] = form
            return render(request, "commerce/checkout.html", context)
        try:
            order = services.place_order(request, form.cleaned_data)
        except services.CartError as exc:
            messages.error(request, str(exc))
            services.clamp_cart_to_stock(request)
            context = _cart_context(request)
            if not context["lines"]:
                return redirect("commerce:cart")
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
        site = SiteSettings.load()
        show_payment_pending = (
            order.payment_method == Order.PaymentMethod.CARD_ONLINE
            and order.payment_status == Order.PaymentStatus.UNPAID
        )
        context = {
            "order": order,
            "dl_events_json": analytics.purchase_events_json(order),
            "thank_you_title": site.thank_you_title_display(),
            "thank_you_number_label": site.thank_you_number_label_display(),
            "thank_you_body": site.thank_you_body_display(order.phone),
            "show_bank_requisites": False,
            "show_payment_pending": show_payment_pending,
            "payment_pending_title": site.payment_pending_title_display(),
            "payment_pending_body": site.payment_pending_body_display(),
            "can_retry_payment": show_payment_pending and get_monobank_service() is not None,
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


@require_GET
def thank_you_purchase_fragment(request, order_number: str):
    """HTMX-опитування: purchase з’являється, коли webhook поставив картку в paid."""
    order = selectors.get_order_for_thanks(request, order_number)
    if order is None:
        return HttpResponse(status=404)
    pending = (
        order.payment_method == Order.PaymentMethod.CARD_ONLINE
        and order.payment_status == Order.PaymentStatus.UNPAID
    )
    return render(
        request,
        "commerce/partials/_purchase_poll.html",
        {
            "order": order,
            "poll_purchase": pending,
            "dl_events_json": None if pending else analytics.purchase_events_json(order),
        },
    )


class PaymentInitView(View):
    """Гість-безпечно: доступ лише за номером зі session['last_order_number'] (SEC-01)."""

    def get(self, request, order_number: str):
        order = selectors.get_order_for_thanks(request, order_number)
        if order is None:
            messages.error(request, _("Замовлення не знайдено"))
            return redirect("commerce:cart")

        mono = get_monobank_service()
        if mono is None:
            messages.warning(
                request,
                _("Оплата карткою тимчасово недоступна — оберіть інший спосіб або зверніться до нас"),
            )
            return redirect("commerce:thank_you", order_number=order.number)

        redirect_url = request.build_absolute_uri(
            reverse("commerce:payment_callback", kwargs={"order_number": order.number}),
        )
        webhook_url = (getattr(settings, "MONOBANK_WEBHOOK_URL", "") or "").strip()
        if not webhook_url:
            webhook_url = request.build_absolute_uri(reverse("commerce:payment_webhook"))

        try:
            checkout = mono.create_invoice(
                order_number=order.number,
                amount=order.total,
                description=f"Замовлення {order.number}",
                redirect_url=redirect_url,
                webhook_url=webhook_url,
            )
        except MonobankError:
            logger.exception("Monobank create_invoice failed for %s", order.number)
            messages.error(request, _("Не вдалося створити оплату. Спробуйте пізніше."))
            return redirect("commerce:thank_you", order_number=order.number)

        Order.objects.filter(pk=order.pk).update(
            payment_intent_id=checkout["invoice_id"],
            updated_at=timezone.now(),
        )
        # Не 302 на Monobank у ланцюгу form POST: CSP form-action 'self' блокує
        # зовнішній редірект після /oformlennya/ → /pay/ (Safari лишається на checkout).
        return render(
            request,
            "commerce/payment_init.html",
            {"order": order, "checkout": checkout},
        )
