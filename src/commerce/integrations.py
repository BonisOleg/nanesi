"""Гачок для CRM/ERP (SalesDrive) — place_order/change_order_status лише пишуть outbox.

Реальний HTTP — salesdrive_stub.process_pending_events (команда або on_commit).
"""
import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from src.commerce.models import Order, OrderIntegrationEvent


def _order_snapshot(order: Order) -> dict:
    return {
        "number": order.number,
        "status": order.status,
        "full_name": order.full_name,
        "phone": order.phone,
        "email": order.email,
        "delivery_method": order.delivery_method,
        "np_city_name": order.np_city_name,
        "np_city_ref": order.np_city_ref,
        "np_warehouse_name": order.np_warehouse_name,
        "np_warehouse_ref": order.np_warehouse_ref,
        "ukrposhta_index": order.ukrposhta_index,
        "ukrposhta_address": order.ukrposhta_address,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "subtotal": order.subtotal,
        "discount_amount": order.discount_amount,
        "shipping_cost": order.shipping_cost,
        "total": order.total,
        "promo_code": order.promo_code_snapshot,
        "comment": order.comment,
        "salesdrive_order_id": order.salesdrive_order_id,
        "items": [
            {
                "name": item.product_name, "sku": item.sku,
                "qty": item.qty, "unit_price": item.unit_price, "line_total": item.line_total,
            }
            for item in order.items.all()
        ],
    }


def queue_order_event(order: Order, event_type: str, *, extra: dict | None = None) -> OrderIntegrationEvent:
    payload = _order_snapshot(order)
    if extra:
        payload.update(extra)
    # JSONField зберігає лише JSON-типи — Decimal/datetime проганяємо через DjangoJSONEncoder.
    payload = json.loads(json.dumps(payload, cls=DjangoJSONEncoder))
    event = OrderIntegrationEvent.objects.create(order=order, event_type=event_type, payload=payload)

    order_pk = order.pk

    def _flush() -> None:
        from src.commerce.salesdrive_stub import process_pending_events

        process_pending_events(limit=20, order_id=order_pk)

    transaction.on_commit(_flush)
    return event
