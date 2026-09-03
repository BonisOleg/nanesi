"""Гачок для CRM/ERP (KeyCRM/SalesDrive) — Доповнення §3 «підготувати», не жива інтеграція.

place_order()/change_order_status() викликають queue_order_event() і більше нічого не
знають про CRM. Коли з'явиться реальний адаптер (обраний сервіс + доступ), він читає
Status.PENDING з OrderIntegrationEvent і сам позначає sent/failed — checkout не міняється.
"""
import json

from django.core.serializers.json import DjangoJSONEncoder

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
        "np_warehouse_name": order.np_warehouse_name,
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
    return OrderIntegrationEvent.objects.create(order=order, event_type=event_type, payload=payload)
