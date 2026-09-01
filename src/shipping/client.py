"""Тонкий клієнт Nova Poshta API v2.0 (novaposhta_skill). Ключ типу «Бізнес-кабінет»
(«Мобільний додаток» не створює ТТН — Фаза 0 скіла).
"""
import logging

import requests

logger = logging.getLogger(__name__)

NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"


class NovaPoshtaError(Exception):
    """Помилка відповіді API (success=false) — завжди з повним текстом errors."""


class NovaPoshtaClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def call(self, model_name: str, called_method: str, method_properties: dict | None = None) -> list:
        payload = {
            "apiKey": self.api_key,
            "modelName": model_name,
            "calledMethod": called_method,
            "methodProperties": method_properties or {},
        }
        response = requests.post(NP_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            errors = data.get("errors") or ["Невідома помилка Нової Пошти"]
            logger.error("NovaPoshta %s.%s failed: %s | props=%s", model_name, called_method, errors, method_properties)
            raise NovaPoshtaError("; ".join(str(e) for e in errors))
        return data.get("data", [])

    # --- Довідники (Фаза 1) ---

    def get_cities(self, page: int = 1, limit: int = 500) -> list:
        # Page ОБОВ'ЯЗКОВО рядком — з int API мовчки повертає 0 записів.
        return self.call("Address", "getCities", {"Page": str(page), "Limit": str(limit)})

    def get_warehouses(self, city_ref: str, page: int = 1, limit: int = 500) -> list:
        return self.call("Address", "getWarehouses", {"CityRef": city_ref, "Page": str(page), "Limit": str(limit)})

    # --- Sender refs, одноразово (Фаза 2) ---

    def get_counterparties(self, counterparty_property: str = "Sender") -> list:
        return self.call("Counterparty", "getCounterparties", {"CounterpartyProperty": counterparty_property})

    def get_counterparty_contact_persons(self, counterparty_ref: str) -> list:
        return self.call("Counterparty", "getCounterpartyContactPersons", {"Ref": counterparty_ref})

    def get_counterparty_addresses(self, counterparty_ref: str, counterparty_property: str = "Sender") -> list:
        return self.call(
            "Counterparty", "getCounterpartyAddresses",
            {"Ref": counterparty_ref, "CounterpartyProperty": counterparty_property},
        )

    # --- Отримувач + ТТН (Фаза 3) ---

    def create_recipient_counterparty(self, *, first_name: str, last_name: str, phone: str) -> dict:
        rows = self.call("Counterparty", "save", {
            "FirstName": first_name,
            "LastName": last_name,
            "MiddleName": "",
            "Phone": phone,
            "CounterpartyType": "PrivatePerson",
            "CounterpartyProperty": "Recipient",
        })
        return rows[0] if rows else {}

    def create_contact_person(self, *, counterparty_ref: str, first_name: str, last_name: str, phone: str) -> dict:
        rows = self.call("ContactPerson", "save", {
            "CounterpartyRef": counterparty_ref,
            "FirstName": first_name,
            "LastName": last_name,
            "MiddleName": "",
            "Phone": phone,
        })
        return rows[0] if rows else {}

    def save_internet_document(self, props: dict) -> dict:
        rows = self.call("InternetDocument", "save", props)
        return rows[0] if rows else {}
