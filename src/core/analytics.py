"""Ecommerce-події для GTM/GA4/Meta Pixel/TikTok Pixel (Доповнення §1 «Пікселі»).

Дані передаються на сторінку через `<script type="application/json">`, а не інлайн
`<script>dataLayer.push(...)</script>` — щоб не порушувати сувору CSP (script-src
'self', без 'unsafe-inline'). static/js/analytics.js сам читає ці блоки і виконує
dataLayer.push / fbq / ttq на клієнті (шаблон: templates/partials/_dl_events.html).
"""
import json

from django.core.serializers.json import DjangoJSONEncoder

SESSION_KEY = "pending_dl_events"


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


def build_event(name: str, *, value=None, currency: str = "UAH", items: list | None = None, extra: dict | None = None) -> dict:
    ecommerce = {"currency": currency}
    if value is not None:
        ecommerce["value"] = float(value)
    if items is not None:
        ecommerce["items"] = items
    if extra:
        ecommerce.update(extra)
    return {"event": name, "ecommerce": ecommerce}


def events_json(events: dict | list[dict]) -> str:
    if isinstance(events, dict):
        events = [events]
    return json.dumps(events, cls=DjangoJSONEncoder)


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
