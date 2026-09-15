"""Синк довідників + створення ТТН.

Фаза 0.5 (novaposhta_skill): без NP_API_KEY — явний ShippingConfigError, НІКОЛИ
демо-дані під видом живих. ТТН — лише після оплати/підтвердження (правило 2 скіла),
викликається з commerce.services.change_order_status, не в момент checkout.
"""
import logging

from django.conf import settings
from django.db import transaction

from src.shipping.client import NovaPoshtaClient, NovaPoshtaError
from src.shipping.models import NPCity, NPWarehouse
from src.shipping.utils import normalize_phone, split_full_name

logger = logging.getLogger(__name__)


class ShippingConfigError(Exception):
    """NP_API_KEY / NP_SENDER_* не налаштовані — не помилка коду, а стан конфігурації."""


class ShippingError(Exception):
    """Помилка виклику API НП під час створення ТТН."""


def get_client() -> NovaPoshtaClient:
    api_key = getattr(settings, "NP_API_KEY", "")
    if not api_key:
        raise ShippingConfigError("NP_API_KEY не налаштовано — інтеграція Нової Пошти вимкнена")
    return NovaPoshtaClient(api_key)


def sync_cities() -> int:
    client = get_client()
    page, total = 1, 0
    while True:
        rows = client.get_cities(page=page)
        if not rows:
            break
        for row in rows:
            NPCity.objects.update_or_create(
                ref=row["Ref"],
                defaults={"name": row["Description"], "area": row.get("AreaDescription", "")},
            )
            total += 1
        page += 1
    return total


def ensure_warehouses_synced(city: NPCity, *, force: bool = False) -> int:
    """Ліниво синкає відділення ОДНОГО міста (не всіх одразу — це тисячі викликів API)."""
    has_rows = city.warehouses.exists()
    needs_category = city.warehouses.filter(category="").exists()
    if not force and has_rows and not needs_category:
        return 0
    try:
        client = get_client()
    except ShippingConfigError:
        if has_rows:
            return 0
        raise
    page, total = 1, 0
    while True:
        rows = client.get_warehouses(city.ref, page=page)
        if not rows:
            break
        for row in rows:
            NPWarehouse.objects.update_or_create(
                ref=row["Ref"],
                defaults={
                    "city": city,
                    "number": row.get("Number", ""),
                    "description": row.get("Description", ""),
                    "category": row.get("CategoryOfWarehouse") or "",
                },
            )
            total += 1
        page += 1
    return total


def _ensure_sender_refs() -> dict:
    required = ("NP_SENDER_REF", "NP_SENDER_CONTACT_REF", "NP_SENDER_CITY_REF", "NP_SENDER_ADDRESS_REF", "NP_SENDER_PHONE")
    values = {name: getattr(settings, name, "") for name in required}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise ShippingConfigError(f"Не заповнені NP_SENDER_*: {', '.join(missing)}")
    return values


def _ensure_recipient(client: NovaPoshtaClient, *, full_name: str, phone: str) -> tuple[str, str]:
    first_name, last_name = split_full_name(full_name)
    phone_norm = normalize_phone(phone)
    counterparty = client.create_recipient_counterparty(first_name=first_name, last_name=last_name, phone=phone_norm)
    recipient_ref = counterparty.get("Ref", "")
    contact_ref = ""
    contacts = counterparty.get("ContactPerson", {}).get("data") if isinstance(counterparty.get("ContactPerson"), dict) else None
    if contacts:
        contact_ref = contacts[0].get("Ref", "")
    if not contact_ref:
        contact = client.create_contact_person(counterparty_ref=recipient_ref, first_name=first_name, last_name=last_name, phone=phone_norm)
        contact_ref = contact.get("Ref", "")
    return recipient_ref, contact_ref


def create_ttn(order_id: int):
    """Ідемпотентно (select_for_update): якщо ttn_number вже є — нічого не робить."""
    from django.utils import timezone

    from src.commerce.models import Order

    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_id)
        if order.ttn_number:
            return order
        if order.delivery_method != Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE:
            raise ShippingError("ТТН створюється лише для доставки Новою Поштою")
        if not order.np_city_ref or not order.np_warehouse_ref:
            message = "Немає Ref міста/відділення НП — довідник ще не синкнуто для цього замовлення"
            order.shipping_error = message
            order.save(update_fields=["shipping_error", "updated_at"])
            raise ShippingError(message)

        try:
            client = get_client()
            sender = _ensure_sender_refs()
            recipient_ref, contact_ref = _ensure_recipient(client, full_name=order.full_name, phone=order.phone)
            props = {
                "PayerType": "Recipient",
                "PaymentMethod": "Cash",
                "DateTime": timezone.localdate().strftime("%d.%m.%Y"),
                "CargoType": "Parcel",
                "Weight": "1",
                "SeatsAmount": "1",
                "ServiceType": "WarehouseWarehouse",
                "Description": f"Замовлення {order.number}",
                "Cost": str(order.total),
                "CitySender": sender["NP_SENDER_CITY_REF"],
                "Sender": sender["NP_SENDER_REF"],
                "SenderAddress": sender["NP_SENDER_ADDRESS_REF"],
                "ContactSender": sender["NP_SENDER_CONTACT_REF"],
                "SendersPhone": sender["NP_SENDER_PHONE"],
                "CityRecipient": order.np_city_ref,
                "RecipientAddress": order.np_warehouse_ref,
                "Recipient": recipient_ref,
                "ContactRecipient": contact_ref,
                "RecipientsPhone": normalize_phone(order.phone),
            }
            result = client.save_internet_document(props)
        except (ShippingConfigError, NovaPoshtaError) as exc:
            order.shipping_error = str(exc)
            order.save(update_fields=["shipping_error", "updated_at"])
            raise ShippingError(str(exc)) from exc

        order.ttn_number = result.get("IntDocNumber", "")
        order.shipping_error = ""
        order.save(update_fields=["ttn_number", "shipping_error", "updated_at"])

        from src.commerce.integrations import queue_order_event
        from src.commerce.models import OrderIntegrationEvent

        queue_order_event(
            order,
            OrderIntegrationEvent.EventType.TTN_UPDATED,
            extra={"ttn_number": order.ttn_number},
        )
        return order


def dispatch_shipment_for_order(order_id: int) -> None:
    """Best-effort — викликається з зміни статусу замовлення. Помилка НЕ повинна
    блокувати сам перехід статусу (менеджер бачить order.shipping_error в адмінці)."""
    try:
        create_ttn(order_id)
    except ShippingConfigError:
        logger.info("ТТН для замовлення %s не створено: НП не налаштована", order_id)
    except ShippingError:
        logger.exception("Помилка створення ТТН для замовлення %s", order_id)
