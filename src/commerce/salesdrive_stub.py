"""Outbox SalesDrive: PENDING → create/update API, без змін checkout.

Без ключів події лишаються PENDING (не «фейковий SENT» як у старому stub).
"""
from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from src.commerce import salesdrive_client as client
from src.commerce import salesdrive_mapper as mapper
from src.commerce.models import Order, OrderIntegrationEvent

logger = logging.getLogger(__name__)


@transaction.atomic
def process_pending_events(*, limit: int = 50, order_id: int | None = None) -> dict:
    if not client.is_configured():
        logger.warning("SalesDrive: SALESDRIVE_API_URL/KEY порожні — outbox не чіпаємо")
        return {"processed": 0, "failed": 0, "skipped": True}

    qs = (
        OrderIntegrationEvent.objects.select_for_update(skip_locked=True)
        .select_related("order")
        .filter(status=OrderIntegrationEvent.Status.PENDING)
        .order_by("created_at")
    )
    if order_id is not None:
        qs = qs.filter(order_id=order_id)
    qs = qs[:limit]

    processed = failed = 0
    for event in qs:
        try:
            _dispatch(event)
            event.status = OrderIntegrationEvent.Status.SENT
            event.sent_at = timezone.now()
            event.error_message = ""
            event.save(update_fields=["payload", "status", "sent_at", "error_message", "updated_at"])
            processed += 1
        except Exception as exc:  # noqa: BLE001 — outbox не рве цикл
            logger.exception("SalesDrive failed for event %s", event.pk)
            event.status = OrderIntegrationEvent.Status.FAILED
            event.error_message = str(exc)[:1000]
            event.save(update_fields=["status", "error_message", "updated_at"])
            failed += 1
    return {"processed": processed, "failed": failed, "skipped": False}


def _dispatch(event: OrderIntegrationEvent) -> None:
    payload = event.payload if isinstance(event.payload, dict) else {}
    order = event.order

    if event.event_type == OrderIntegrationEvent.EventType.ORDER_CREATED:
        body = mapper.build_create_payload(payload)
        response = client.create_order(body)
        sd_id = client.extract_order_id(response)
        receipt = {"ok": True, "response": response, "salesdrive_order_id": sd_id}
        payload = dict(payload)
        payload["_salesdrive_receipt"] = receipt
        event.payload = payload
        if sd_id and not order.salesdrive_order_id:
            Order.objects.filter(pk=order.pk).update(salesdrive_order_id=sd_id)
            order.salesdrive_order_id = sd_id
        return

    if event.event_type == OrderIntegrationEvent.EventType.STATUS_CHANGED:
        to_status = payload.get("to_status") or payload.get("status")
        pay = payload.get("payment_method")
        body = mapper.build_update_payload(
            external_id=str(payload.get("number") or order.number),
            salesdrive_order_id=order.salesdrive_order_id,
            site_status=str(to_status) if to_status else None,
            payment_method=str(pay) if pay else None,
        )
        if not body.get("data"):
            raise client.SalesDriveError("Немає полів для update (status/payment)")
        response = client.update_order(body)
        payload = dict(payload)
        payload["_salesdrive_receipt"] = {"ok": True, "response": response}
        event.payload = payload
        return

    if event.event_type == OrderIntegrationEvent.EventType.TTN_UPDATED:
        ttn = str(payload.get("ttn_number") or order.ttn_number or "").strip()
        if not ttn:
            raise client.SalesDriveError("Порожній ТТН у події")
        body = mapper.build_update_payload(
            external_id=str(payload.get("number") or order.number),
            salesdrive_order_id=order.salesdrive_order_id,
            ttn_number=ttn,
            delivery_method=str(payload.get("delivery_method") or order.delivery_method),
        )
        response = client.update_order(body)
        payload = dict(payload)
        payload["_salesdrive_receipt"] = {"ok": True, "response": response}
        event.payload = payload
        return

    raise client.SalesDriveError(f"Невідомий event_type={event.event_type}")
