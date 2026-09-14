"""HTTP-клієнт SalesDrive: створення заявки (/handler/) і оновлення (/api/order/update/)."""
from __future__ import annotations

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30


class SalesDriveError(Exception):
    """Помилка відповіді або конфігурації SalesDrive."""


def is_configured() -> bool:
    return bool(getattr(settings, "SALESDRIVE_API_URL", "") and getattr(settings, "SALESDRIVE_API_KEY", ""))


def _base_url() -> str:
    url = (getattr(settings, "SALESDRIVE_API_URL", "") or "").rstrip("/")
    if not url:
        raise SalesDriveError("SALESDRIVE_API_URL не задано")
    return url


def _headers() -> dict:
    key = getattr(settings, "SALESDRIVE_API_KEY", "") or ""
    if not key:
        raise SalesDriveError("SALESDRIVE_API_KEY не задано")
    return {
        "X-Api-Key": key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def create_order(payload: dict) -> dict:
    """POST /handler/ → {"success": true, "data": {"orderId": N, ...}}."""
    url = f"{_base_url()}/handler/"
    response = requests.post(url, headers=_headers(), json=payload, timeout=DEFAULT_TIMEOUT)
    return _parse_response(response, action="create")


def update_order(payload: dict) -> dict:
    """POST /api/order/update/."""
    url = f"{_base_url()}/api/order/update/"
    response = requests.post(url, headers=_headers(), json=payload, timeout=DEFAULT_TIMEOUT)
    return _parse_response(response, action="update")


def _parse_response(response: requests.Response, *, action: str) -> dict:
    try:
        data = response.json()
    except ValueError as exc:
        raise SalesDriveError(
            f"SalesDrive {action}: не JSON (HTTP {response.status_code}): {response.text[:300]}"
        ) from exc

    if response.status_code >= 400:
        raise SalesDriveError(f"SalesDrive {action}: HTTP {response.status_code}: {data}")

    if isinstance(data, dict) and data.get("success") is False:
        raise SalesDriveError(f"SalesDrive {action}: {data}")

    if isinstance(data, dict) and data.get("status") == "error":
        raise SalesDriveError(f"SalesDrive {action}: {data.get('message') or data}")

    return data if isinstance(data, dict) else {"raw": data}


def extract_order_id(response: dict) -> int | None:
    data = response.get("data")
    if isinstance(data, dict):
        oid = data.get("orderId") or data.get("id")
        if oid is not None:
            return int(oid)
    oid = response.get("orderId") or response.get("id")
    return int(oid) if oid is not None else None
