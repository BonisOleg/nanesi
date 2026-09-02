"""Заглушка SalesDrive / KeyCRM — без API-ключів лише маркує outbox.

Коли з'являться дані доступу: замінити `_send_payload` на реальний HTTP-клієнт,
не змінюючи checkout / queue_order_event.
"""
from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone

from src.commerce.models import OrderIntegrationEvent

logger = logging.getLogger(__name__)


def _send_payload(payload: dict) -> dict:
    """Заглушка транспорту. Повертає фейковий receipt."""
    logger.info("SalesDrive STUB send keys=%s", sorted(payload.keys()))
    return {"ok": True, "stub": True, "received_at": timezone.now().isoformat()}


@transaction.atomic
def process_pending_events(*, limit: int = 50) -> dict:
    """Обробити PENDING події outbox. Ідемпотентно для вже sent."""
    qs = (
        OrderIntegrationEvent.objects.select_for_update(skip_locked=True)
        .filter(status=OrderIntegrationEvent.Status.PENDING)
        .order_by("created_at")[:limit]
    )
    processed = failed = 0
    for event in qs:
        try:
            receipt = _send_payload(event.payload if isinstance(event.payload, dict) else {})
            # Зберігаємо receipt у payload, щоб не розширювати схему до появи реального API.
            payload = dict(event.payload or {})
            payload["_stub_receipt"] = receipt
            event.payload = payload
            event.status = OrderIntegrationEvent.Status.SENT
            event.sent_at = timezone.now()
            event.error_message = ""
            event.save(update_fields=["payload", "status", "sent_at", "error_message", "updated_at"])
            processed += 1
        except Exception as exc:  # noqa: BLE001 — outbox не повинен рвати цикл
            logger.exception("SalesDrive stub failed for event %s", event.pk)
            event.status = OrderIntegrationEvent.Status.FAILED
            event.error_message = str(exc)[:1000]
            event.save(update_fields=["status", "error_message", "updated_at"])
            failed += 1
    return {"processed": processed, "failed": failed}
