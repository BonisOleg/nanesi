"""Monobank Acquiring: create invoice + webhook idempotency (без реального API)."""
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from src.commerce.models import Order
from src.commerce.payments.monobank import MonobankService, webhook_idempotency_key


class MonobankServiceTests(TestCase):
    @patch("src.commerce.payments.monobank.requests.post")
    def test_create_invoice_converts_uah_to_kopiyky(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"invoiceId": "inv_1", "pageUrl": "https://pay.mbnk.biz/inv_1"},
        )
        service = MonobankService("token", webhook_url="https://example.com/hook")
        result = service.create_invoice(
            order_number="N-1",
            amount=Decimal("10.50"),
            description="Замовлення N-1",
            redirect_url="https://example.com/back",
        )
        self.assertEqual(result["invoice_id"], "inv_1")
        body = mock_post.call_args.kwargs["json"]
        self.assertEqual(body["amount"], 1050)
        self.assertEqual(body["merchantPaymInfo"]["reference"], "N-1")
        self.assertEqual(body["webHookUrl"], "https://example.com/hook")


@override_settings(MONOBANK_TOKEN="test-token")
class MonobankWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.order = Order.objects.create(
            full_name="Тест",
            phone="+380501112233",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CARD_ONLINE,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_intent_id="inv_abc",
            total=Decimal("100.00"),
        )
        # фіксуємо номер після автогенерації NS-…
        Order.objects.filter(pk=self.order.pk).update(number="ORD-MONO-1")
        self.order.refresh_from_db()

    @patch("src.commerce.views.get_monobank_service")
    def test_success_webhook_marks_paid(self, mock_get):
        mono = MagicMock()
        mono.verify_webhook.return_value = True
        mock_get.return_value = mono
        payload = {
            "invoiceId": "inv_abc",
            "status": "success",
            "reference": "ORD-MONO-1",
            "modifiedDate": "2026-11-09T10:00:00Z",
        }
        body = json.dumps(payload).encode()
        response = self.client.post(
            reverse("commerce:payment_webhook"),
            data=body,
            content_type="application/json",
            headers={"X-Sign": "dGVzdA=="},
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.PAID)
        self.assertEqual(self.order.payment_idempotency_key, webhook_idempotency_key(payload))
        self.assertIsNotNone(self.order.paid_at)

    @patch("src.commerce.views.get_monobank_service")
    def test_invalid_sign_rejected(self, mock_get):
        mono = MagicMock()
        mono.verify_webhook.return_value = False
        mock_get.return_value = mono
        response = self.client.post(
            reverse("commerce:payment_webhook"),
            data=b'{"invoiceId":"inv_abc","status":"success"}',
            content_type="application/json",
            headers={"X-Sign": "bad"},
        )
        self.assertEqual(response.status_code, 403)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.UNPAID)
