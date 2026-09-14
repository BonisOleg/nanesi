"""Обробка webhook SalesDrive (status_change → статус замовлення на сайті)."""
from __future__ import annotations

import logging

from django.db import transaction

from src.commerce import salesdrive_mapper as mapper
from src.commerce.models import Order
from src.commerce.services import change_order_status

logger = logging.getLogger(__name__)


class SalesDriveWebhookError(Exception):
    def __init__(self, message: str, *, http_status: int = 400):
        super().__init__(message)
        self.http_status = http_status


def handle_salesdrive_webhook(body: dict) -> dict:
    """Повертає dict з результатом для JSON-відповіді. Кидає SalesDriveWebhookError."""
    info = body.get("info") if isinstance(body.get("info"), dict) else {}
    data = body.get("data") if isinstance(body.get("data"), dict) else {}

    event = str(info.get("webhookEvent") or "")
    if event == "new_order":
        return {"ok": True, "ignored": True, "reason": "new_order"}
    if event != "status_change":
        return {"ok": True, "ignored": True, "reason": f"event:{event or 'empty'}"}

    status_id = data.get("statusId")
    target = mapper.site_status_from_sd(status_id)
    if target is None:
        return {"ok": True, "ignored": True, "reason": f"statusId:{status_id}"}

    order = _find_order(data)
    if order is None:
        raise SalesDriveWebhookError("order not found", http_status=404)

    sd_id = data.get("id")
    if sd_id and not order.salesdrive_order_id:
        try:
            Order.objects.filter(pk=order.pk, salesdrive_order_id__isnull=True).update(
                salesdrive_order_id=int(sd_id),
            )
            order.salesdrive_order_id = int(sd_id)
        except (TypeError, ValueError):
            pass

    # Анти-ехо: сайт paid → SD «Підтверджено»(2) → webhook не відкочує на confirmed.
    if target == Order.Status.CONFIRMED and order.status == Order.Status.PAID:
        return {
            "ok": True, "ignored": True, "reason": "paid_echo_guard",
            "order": order.number, "status": order.status,
        }

    if order.status == target:
        return {"ok": True, "unchanged": True, "order": order.number, "status": order.status}

    with transaction.atomic():
        locked = Order.objects.select_for_update().filter(pk=order.pk).first()
        if locked is None:
            raise SalesDriveWebhookError("order not found", http_status=404)
        if locked.status == target:
            return {"ok": True, "unchanged": True, "order": locked.number, "status": locked.status}
        if target == Order.Status.CONFIRMED and locked.status == Order.Status.PAID:
            return {
                "ok": True, "ignored": True, "reason": "paid_echo_guard",
                "order": locked.number, "status": locked.status,
            }
        change_order_status(
            locked,
            target,
            note=f"SalesDrive webhook statusId={status_id}",
            enqueue_crm=False,
            force=True,
        )
        locked.refresh_from_db()
        logger.info(
            "SalesDrive webhook: %s → %s (sd statusId=%s)",
            locked.number, locked.status, status_id,
        )
        return {"ok": True, "order": locked.number, "status": locked.status, "from_sd_statusId": status_id}


def _find_order(data: dict) -> Order | None:
    sd_id = data.get("id")
    if sd_id is not None:
        try:
            order = Order.objects.filter(salesdrive_order_id=int(sd_id)).first()
            if order:
                return order
        except (TypeError, ValueError):
            pass

    external = data.get("externalId") or data.get("external_id")
    if external:
        order = Order.objects.filter(number=str(external)).first()
        if order:
            return order
    return None
