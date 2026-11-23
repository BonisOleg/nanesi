"""Webhook-и оплати та CRM — окремо від cart/checkout views (ліміт 500 рядків)."""
import hmac
import json
import logging

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from src.commerce import services
from src.commerce.models import Order
from src.commerce.payments.monobank import get_monobank_service, webhook_idempotency_key

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def payment_webhook(request):
    """SEC-07: єдине джерело істини — webhook Monobank з X-Sign (ECDSA)."""
    mono = get_monobank_service()
    if mono is None:
        return HttpResponse("Monobank not configured", status=503)

    x_sign = request.headers.get("X-Sign") or request.META.get("HTTP_X_SIGN", "")
    body = request.body or b""
    if not x_sign or not mono.verify_webhook(body, x_sign):
        return HttpResponse("Invalid signature", status=403)

    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, TypeError):
        return HttpResponse("Invalid JSON", status=400)

    if not isinstance(payload, dict):
        return HttpResponse("Invalid payload", status=400)

    invoice_id = str(payload.get("invoiceId") or "")
    status = str(payload.get("status") or "")
    reference = str(payload.get("reference") or "")
    if not reference:
        paym_info = payload.get("merchantPaymInfo")
        if isinstance(paym_info, dict):
            reference = str(paym_info.get("reference") or "")
    if not invoice_id and not reference:
        return HttpResponse("Missing invoice/reference", status=400)

    with transaction.atomic():
        order_qs = Order.objects.select_for_update()
        order = None
        if invoice_id:
            order = order_qs.filter(payment_intent_id=invoice_id).first()
        if order is None and reference:
            order = order_qs.filter(number=reference).first()
        if order is None:
            return HttpResponse("Order not found", status=404)

        idem_key = webhook_idempotency_key(payload)
        if order.payment_idempotency_key == idem_key:
            return HttpResponse("OK (idempotent)", status=200)

        if status == "success":
            _apply_monobank_success(order, invoice_id, idem_key)
        elif status in ("failure", "reversed", "expired"):
            _apply_monobank_failure(order, invoice_id, idem_key, status)

    return HttpResponse("OK", status=200)


def _apply_monobank_success(order: Order, invoice_id: str, idem_key: str) -> None:
    if order.status == Order.Status.CANCELLED:
        logger.warning(
            "Monobank success on cancelled order %s — ignore paid",
            order.number,
        )
        order.payment_idempotency_key = idem_key
        if invoice_id and not order.payment_intent_id:
            order.payment_intent_id = invoice_id
        order.save(update_fields=["payment_idempotency_key", "payment_intent_id", "updated_at"])
        return
    order.payment_status = Order.PaymentStatus.PAID
    order.payment_intent_id = invoice_id or order.payment_intent_id
    order.payment_idempotency_key = idem_key
    order.paid_at = timezone.now()
    order.save()
    try:
        services.change_order_status(order, Order.Status.PAID)
    except services.OrderStatusError:
        pass


def _apply_monobank_failure(order: Order, invoice_id: str, idem_key: str, status: str) -> None:
    order.payment_idempotency_key = idem_key
    update_fields = ["payment_idempotency_key", "updated_at"]
    if invoice_id and not order.payment_intent_id:
        order.payment_intent_id = invoice_id
        update_fields.append("payment_intent_id")
    order.save(update_fields=update_fields)
    # failure/reversed — невдала спроба, клієнт ще може оплатити той самий інвойс.
    # Скасовуємо і повертаємо склад лише коли рахунок прострочений.
    if (
        status == "expired"
        and order.status != Order.Status.CANCELLED
        and order.payment_status == Order.PaymentStatus.UNPAID
    ):
        try:
            services.change_order_status(
                order,
                Order.Status.CANCELLED,
                note=f"Monobank {status}",
            )
        except services.OrderStatusError:
            logger.warning(
                "Cannot cancel order %s after Monobank %s",
                order.number,
                status,
            )


@csrf_exempt
def payment_callback(request, order_number: str):
    """result_url — лише UX-редирект, статус нею НЕ встановлюється (SEC-07)."""
    order = get_object_or_404(Order, number=order_number)
    return redirect("commerce:thank_you", order_number=order.number)


@csrf_exempt
@require_POST
def salesdrive_webhook(request, token: str):
    """SalesDrive → сайт: лише status_change. Секрет у шляху (SALESDRIVE_WEBHOOK_SECRET)."""
    from src.commerce.salesdrive_webhook import SalesDriveWebhookError, handle_salesdrive_webhook

    expected = getattr(settings, "SALESDRIVE_WEBHOOK_SECRET", "") or ""
    if not expected or not hmac.compare_digest(token, expected):
        return JsonResponse({"ok": False, "error": "forbidden"}, status=403)

    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "invalid json"}, status=400)
    if not isinstance(body, dict):
        return JsonResponse({"ok": False, "error": "invalid body"}, status=400)

    try:
        result = handle_salesdrive_webhook(body)
    except SalesDriveWebhookError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=exc.http_status)
    except Exception:
        logger.exception("SalesDrive webhook failed")
        return JsonResponse({"ok": False, "error": "internal"}, status=500)
    return JsonResponse(result, status=200)
