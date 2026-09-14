"""Мапінг полів сайту → SalesDrive (довідники nanesi.salesdrive.me, зняті по API).

Оплата (parameter):
  card_online → tocard (Картка Приватбанку) — найближчий до онлайн-оплати
  cod → postpay
  bank_transfer → noncash

Доставка (parameter):
  np_warehouse → novaposhta
  ukrposhta → ukrposhta

Статуси (id):
  new → 1 Новий
  confirmed → 2 Підтверджено
  paid → 2 Підтверджено (окремого «Оплачено» в SD немає)
  assembling → 3 На відправку
  shipped → 4 Відправлено
  delivered → 5 Продаж
  cancelled → 6 Відмова
"""
from __future__ import annotations

PAYMENT_METHOD_PARAM = {
    "card_online": "tocard",
    "cod": "postpay",
    "bank_transfer": "noncash",
}

DELIVERY_METHOD_PARAM = {
    "np_warehouse": "novaposhta",
    "ukrposhta": "ukrposhta",
}

STATUS_ID = {
    "new": 1,
    "confirmed": 2,
    "paid": 2,
    "assembling": 3,
    "shipped": 4,
    "delivered": 5,
    "cancelled": 6,
}

# Зворотний мапінг webhook status_change (7/8 — ігнор у handler).
STATUS_FROM_SD = {
    1: "new",
    2: "confirmed",
    3: "assembling",
    4: "shipped",
    5: "delivered",
    6: "cancelled",
}
STATUS_FROM_SD_IGNORED = frozenset({7, 8})  # Повернення, Видалений


def site_status_from_sd(status_id) -> str | None:
    """None = ігнорувати (невідомий або 7/8)."""
    try:
        sid = int(status_id)
    except (TypeError, ValueError):
        return None
    if sid in STATUS_FROM_SD_IGNORED:
        return None
    return STATUS_FROM_SD.get(sid)


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = (full_name or "").strip().split(None, 1)
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]


def shipping_address_from_payload(payload: dict) -> str:
    method = payload.get("delivery_method")
    if method == "np_warehouse":
        city = (payload.get("np_city_name") or "").strip()
        wh = (payload.get("np_warehouse_name") or "").strip()
        return ", ".join(p for p in (city, wh) if p)
    if method == "ukrposhta":
        idx = (payload.get("ukrposhta_index") or "").strip()
        addr = (payload.get("ukrposhta_address") or "").strip()
        return ", ".join(p for p in (idx, addr) if p)
    return ""


def novaposhta_block(payload: dict) -> dict | None:
    if payload.get("delivery_method") != "np_warehouse":
        return None
    block: dict = {"ServiceType": "Warehouse"}
    wh_ref = (payload.get("np_warehouse_ref") or "").strip()
    wh_name = (payload.get("np_warehouse_name") or "").strip()
    city_ref = (payload.get("np_city_ref") or "").strip()
    city_name = (payload.get("np_city_name") or "").strip()
    if wh_ref:
        block["WarehouseNumber"] = wh_ref
    elif wh_name:
        block["WarehouseNumber"] = wh_name
    if city_ref:
        block["city"] = city_ref
    elif city_name:
        block["city"] = city_name
        block["cityNameFormat"] = "short"
    return block if "WarehouseNumber" in block or "city" in block else None


def ukrposhta_block(payload: dict) -> dict | None:
    if payload.get("delivery_method") != "ukrposhta":
        return None
    block: dict = {"ServiceType": "Doors"}
    idx = (payload.get("ukrposhta_index") or "").strip()
    addr = (payload.get("ukrposhta_address") or "").strip()
    if idx:
        block["WarehouseNumber"] = idx
    if addr:
        # SD очікує структуровані поля; текст адреси дублюємо в shipping_address.
        block["Street"] = addr
    return block if idx or addr else None


def build_create_payload(payload: dict) -> dict:
    """payload — снепшот з OrderIntegrationEvent (integrations._order_snapshot)."""
    f_name, l_name = split_full_name(str(payload.get("full_name") or ""))
    products = []
    for item in payload.get("items") or []:
        sku = str(item.get("sku") or "")
        products.append({
            "id": sku or str(item.get("name") or "item"),
            "name": str(item.get("name") or sku or "Товар"),
            "sku": sku,
            "costPerItem": float(item.get("unit_price") or 0),
            "amount": float(item.get("qty") or 1),
        })

    body: dict = {
        "getResultData": 1,
        "fName": f_name,
        "lName": l_name,
        "phone": str(payload.get("phone") or ""),
        "email": str(payload.get("email") or ""),
        "externalId": str(payload.get("number") or ""),
        "comment": str(payload.get("comment") or ""),
        "products": products,
    }
    pay = PAYMENT_METHOD_PARAM.get(str(payload.get("payment_method") or ""))
    if pay:
        body["payment_method"] = pay
    ship = DELIVERY_METHOD_PARAM.get(str(payload.get("delivery_method") or ""))
    if ship:
        body["shipping_method"] = ship
    addr = shipping_address_from_payload(payload)
    if addr:
        body["shipping_address"] = addr
    np_block = novaposhta_block(payload)
    if np_block:
        body["novaposhta"] = np_block
    up_block = ukrposhta_block(payload)
    if up_block:
        body["ukrposhta"] = up_block
    return body


def build_update_payload(
    *,
    external_id: str,
    salesdrive_order_id: int | None,
    site_status: str | None = None,
    payment_method: str | None = None,
    comment: str | None = None,
) -> dict:
    data: dict = {}
    if site_status:
        sid = STATUS_ID.get(site_status)
        if sid is not None:
            data["statusId"] = sid
    if payment_method:
        pay = PAYMENT_METHOD_PARAM.get(payment_method)
        if pay:
            data["payment_method"] = pay
    if comment:
        data["comment"] = comment

    body: dict = {"data": data}
    if salesdrive_order_id:
        body["id"] = int(salesdrive_order_id)
    else:
        body["externalId"] = external_id
    return body
