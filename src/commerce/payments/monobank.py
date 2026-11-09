"""Monobank Acquiring. SEC-07: статус оплати лише через webhook з перевіркою X-Sign."""
from __future__ import annotations

import base64
import hashlib
import logging
from decimal import Decimal

import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings

logger = logging.getLogger(__name__)

API_BASE = "https://api.monobank.ua"
CCY_UAH = 980


class MonobankError(Exception):
    """Помилка конфігурації або відповіді Monobank Acquiring."""


class MonobankService:
    def __init__(self, token: str, *, webhook_url: str = ""):
        self.token = token
        self.webhook_url = (webhook_url or "").strip()
        self._pubkey_pem: bytes | None = None

    def _headers(self) -> dict[str, str]:
        return {
            "X-Token": self.token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def create_invoice(
        self,
        *,
        order_number: str,
        amount: Decimal | float | str,
        description: str,
        redirect_url: str,
        webhook_url: str | None = None,
    ) -> dict:
        """POST /api/merchant/invoice/create → invoiceId + pageUrl. amount у гривнях."""
        amount_kop = int((Decimal(str(amount)) * 100).quantize(Decimal("1")))
        if amount_kop <= 0:
            raise MonobankError("Сума інвойсу має бути > 0")

        body: dict = {
            "amount": amount_kop,
            "ccy": CCY_UAH,
            "merchantPaymInfo": {
                "reference": order_number,
                "destination": description[:200],
            },
            "redirectUrl": redirect_url,
        }
        hook = (webhook_url if webhook_url is not None else self.webhook_url).strip()
        if hook:
            body["webHookUrl"] = hook

        response = requests.post(
            f"{API_BASE}/api/merchant/invoice/create",
            headers=self._headers(),
            json=body,
            timeout=30,
        )
        data = self._parse_json(response, action="invoice/create")
        invoice_id = data.get("invoiceId")
        page_url = data.get("pageUrl")
        if not invoice_id or not page_url:
            raise MonobankError(f"Неповна відповідь create invoice: {data}")
        return {"invoice_id": str(invoice_id), "page_url": str(page_url), "raw": data}

    def get_invoice_status(self, invoice_id: str) -> dict:
        response = requests.get(
            f"{API_BASE}/api/merchant/invoice/status",
            headers=self._headers(),
            params={"invoiceId": invoice_id},
            timeout=30,
        )
        return self._parse_json(response, action="invoice/status")

    def fetch_pubkey(self) -> bytes:
        response = requests.get(
            f"{API_BASE}/api/merchant/pubkey",
            headers=self._headers(),
            timeout=30,
        )
        data = self._parse_json(response, action="pubkey")
        key_b64 = data.get("key") or data.get("pubkey") or ""
        if not key_b64:
            raise MonobankError(f"Порожній pubkey: {data}")
        pem = base64.b64decode(key_b64)
        self._pubkey_pem = pem
        return pem

    def verify_webhook(self, body: bytes, x_sign_b64: str, *, pubkey_pem: bytes | None = None) -> bool:
        """ECDSA SHA256: X-Sign = base64(DER), ключ з /api/merchant/pubkey."""
        pem = pubkey_pem or self._pubkey_pem
        if pem is None:
            try:
                pem = self.fetch_pubkey()
            except MonobankError:
                logger.exception("Monobank pubkey fetch failed")
                return False
        try:
            signature = base64.b64decode(x_sign_b64)
            public_key = serialization.load_pem_public_key(pem)
            if not isinstance(public_key, ec.EllipticCurvePublicKey):
                logger.warning("Monobank pubkey is not ECDSA")
                return False
            public_key.verify(signature, body, ec.ECDSA(hashes.SHA256()))
            return True
        except (InvalidSignature, ValueError, TypeError) as exc:
            logger.warning("Monobank X-Sign invalid: %s", exc)
            return False

    @staticmethod
    def _parse_json(response: requests.Response, *, action: str) -> dict:
        try:
            data = response.json()
        except ValueError as exc:
            raise MonobankError(
                f"Monobank {action}: не JSON (HTTP {response.status_code}): {response.text[:300]}"
            ) from exc
        if response.status_code >= 400:
            raise MonobankError(f"Monobank {action}: HTTP {response.status_code}: {data}")
        if not isinstance(data, dict):
            raise MonobankError(f"Monobank {action}: неочікувана відповідь {data!r}")
        err = data.get("errCode") or data.get("errorDescription")
        if err and response.status_code >= 400:
            raise MonobankError(f"Monobank {action}: {err}")
        return data


def get_monobank_service() -> MonobankService | None:
    token = (getattr(settings, "MONOBANK_TOKEN", "") or "").strip()
    if not token:
        return None
    webhook = (getattr(settings, "MONOBANK_WEBHOOK_URL", "") or "").strip()
    return MonobankService(token, webhook_url=webhook)


def webhook_idempotency_key(payload: dict) -> str:
    invoice_id = str(payload.get("invoiceId") or "")
    status = str(payload.get("status") or "")
    modified = str(payload.get("modifiedDate") or "")
    raw = f"{invoice_id}|{status}|{modified}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
    return f"mono_{digest}"
