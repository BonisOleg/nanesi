"""Ecommerce-події для GTM/GA4/Meta Pixel/TikTok Pixel (Доповнення §1 «Пікселі»).

Дані передаються на сторінку через `<script type="application/json">`, а не інлайн
`<script>dataLayer.push(...)</script>` — щоб не порушувати сувору CSP (script-src
'self', без 'unsafe-inline'). static/js/analytics.js сам читає ці блоки і виконує
dataLayer.push / fbq / ttq на клієнті (шаблон: templates/partials/_dl_events.html).
"""
import json
import re

from django.core.serializers.json import DjangoJSONEncoder

from src.core.validators import escape_json_for_html

SESSION_KEY = "pending_dl_events"
CARD_ONLINE = "card_online"
PAID = "paid"


def make_item(*, item_id, item_name, price, quantity=1, brand=None, category=None) -> dict:
    item = {
        "item_id": str(item_id),
        "item_name": item_name,
        "price": float(price) if price is not None else None,
        "quantity": quantity,
    }
    if brand:
        item["item_brand"] = brand
    if category:
        item["item_category"] = category
    return item


def build_event(
    name: str,
    *,
    value=None,
    currency: str = "UAH",
    items: list | None = None,
    extra: dict | None = None,
    user_data: dict | None = None,
) -> dict:
    ecommerce = {"currency": currency}
    if value is not None:
        ecommerce["value"] = float(value)
    if items is not None:
        ecommerce["items"] = items
    if extra:
        ecommerce.update(extra)
    payload = {"event": name, "ecommerce": ecommerce}
    if user_data:
        payload["user_data"] = user_data
    return payload


def events_json(events: dict | list[dict]) -> str:
    if isinstance(events, dict):
        events = [events]
    return escape_json_for_html(json.dumps(events, cls=DjangoJSONEncoder, ensure_ascii=False))


def queue_event(request, event: dict) -> None:
    """Для дій, після яких іде redirect (напр. cart_add без HTMX) — подія доживає до наступного рендеру."""
    events = request.session.get(SESSION_KEY, [])
    events.append(event)
    request.session[SESSION_KEY] = events
    request.session.modified = True


def pop_events(request) -> list[dict]:
    return request.session.pop(SESSION_KEY, [])


def attach_pending_events(context: dict, request) -> dict:
    events = pop_events(request)
    if events:
        context["dl_events_json"] = events_json(events)
    return context


def phone_to_e164(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        return ""
    if digits.startswith("380"):
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 10:
        return f"+380{digits[1:]}"
    if len(digits) == 9:
        return f"+380{digits}"
    return f"+{digits}"


def user_data_from_contact(*, email: str = "", phone: str = "") -> dict:
    data = {}
    email_value = (email or "").strip()
    e164 = phone_to_e164(phone)
    if email_value:
        data["email"] = email_value
    if e164:
        data["phone_number"] = e164
    return data


def should_track_purchase(order) -> bool:
    if getattr(order, "payment_method", "") == CARD_ONLINE:
        return getattr(order, "payment_status", "") == PAID
    return True


def _item_from_order_line(item) -> dict:
    variant = getattr(item, "product_variant", None)
    product = getattr(variant, "product", None) if variant else None
    brand = getattr(getattr(product, "brand", None), "name", None)
    category = getattr(getattr(product, "category", None), "name", None)
    return make_item(
        item_id=item.sku,
        item_name=item.product_name,
        price=item.unit_price,
        quantity=item.qty,
        brand=brand,
        category=category,
    )


def purchase_event(order) -> dict:
    return build_event(
        "purchase",
        value=order.total,
        items=[_item_from_order_line(item) for item in order.items.all()],
        extra={
            "transaction_id": order.number,
            "shipping": float(order.shipping_cost) if order.shipping_cost else 0,
            "coupon": order.promo_code_snapshot or None,
        },
        user_data=user_data_from_contact(email=order.email, phone=order.phone) or None,
    )


def purchase_events_json(order) -> str | None:
    if not should_track_purchase(order):
        return None
    return events_json(purchase_event(order))
