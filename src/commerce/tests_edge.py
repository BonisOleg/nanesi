"""Edge-case: merge кошика, склад, double-submit, промо max_uses, TTL картки."""
import json
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client, TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from src.catalog.models import Brand, Category, Product, ProductVariant
from src.commerce.models import Cart, CartItem, Order, OrderItem, PromoCode
from src.commerce.payments.monobank import webhook_idempotency_key
from src.commerce.services import merge_guest_cart
from src.content.models import SiteSettings

User = get_user_model()


def _catalog_variant(*, sku: str, stock: int, price: str = "200.00") -> ProductVariant:
    brand, _ = Brand.objects.get_or_create(name="EdgeBrand", slug="edge-brand")
    category, _ = Category.objects.get_or_create(name="EdgeCat", slug="edge-cat")
    product = Product.objects.create(
        name=f"Товар {sku}",
        slug=f"tovar-{sku.lower()}",
        brand=brand,
        category=category,
        is_active=True,
    )
    return ProductVariant.objects.create(
        product=product,
        sku=sku,
        retail_price=Decimal(price),
        stock_quantity=stock,
        is_active=True,
    )


def _enable_checkout() -> None:
    site = SiteSettings.load()
    site.nova_poshta_enabled = True
    site.ukrposhta_enabled = True
    site.cash_on_delivery_enabled = True
    site.save(update_fields=[
        "nova_poshta_enabled", "ukrposhta_enabled", "cash_on_delivery_enabled",
    ])


def _checkout_payload(**extra) -> dict:
    data = {
        "full_name": "Тест Тестенко",
        "phone": "380501112233",
        "email": "edge@test.test",
        "delivery_method": "ukrposhta",
        "ukrposhta_index": "01001",
        "ukrposhta_address": "Київ, Хрещатик 1",
        "payment_method": "cod",
        "privacy_consent": "on",
        "comment": "",
    }
    data.update(extra)
    return data


class MergeGuestCartTests(TestCase):
    def test_sum_qty_capped_at_stock(self):
        variant = _catalog_variant(sku="EDGE-MERGE-1", stock=3)
        user = User.objects.create_user(
            username="merge-user", email="merge@test.test", password="NanesiEdge1",
        )
        guest_cart = Cart.objects.create(session_key="guest-merge-key", status=Cart.Status.OPEN)
        user_cart = Cart.objects.create(user=user, status=Cart.Status.OPEN)
        CartItem.objects.create(cart=guest_cart, product_variant=variant, qty=2)
        CartItem.objects.create(cart=user_cart, product_variant=variant, qty=2)

        merged = merge_guest_cart(user, "guest-merge-key")
        item = merged.items.get(product_variant=variant)
        self.assertEqual(item.qty, 3)
        guest_cart.refresh_from_db()
        self.assertEqual(guest_cart.status, Cart.Status.CONVERTED)

    def test_different_sku_keeps_both_lines(self):
        a = _catalog_variant(sku="EDGE-MERGE-A", stock=5)
        b = _catalog_variant(sku="EDGE-MERGE-B", stock=5)
        user = User.objects.create_user(
            username="merge-user-2", email="merge2@test.test", password="NanesiEdge1",
        )
        guest_cart = Cart.objects.create(session_key="guest-merge-2", status=Cart.Status.OPEN)
        user_cart = Cart.objects.create(user=user, status=Cart.Status.OPEN)
        CartItem.objects.create(cart=guest_cart, product_variant=a, qty=1)
        CartItem.objects.create(cart=user_cart, product_variant=b, qty=1)

        merged = merge_guest_cart(user, "guest-merge-2")
        skus = set(merged.items.values_list("product_variant__sku", flat=True))
        self.assertEqual(skus, {"EDGE-MERGE-A", "EDGE-MERGE-B"})

    def test_login_merges_guest_cart(self):
        _enable_checkout()
        variant = _catalog_variant(sku="EDGE-LOGIN-1", stock=5)
        User.objects.create_user(
            username="login-merge", email="login-merge@test.test", password="NanesiEdge1",
        )
        self.client.post(reverse("commerce:cart_add", args=[variant.pk]), {"qty": 1})
        response = self.client.post(reverse("accounts:login"), {
            "form": "login",
            "username": "login-merge@test.test",
            "password": "NanesiEdge1",
        })
        self.assertEqual(response.status_code, 302)
        cart = Cart.objects.get(user__email="login-merge@test.test", status=Cart.Status.OPEN)
        self.assertEqual(cart.items.get(product_variant=variant).qty, 1)


class StockAndCheckoutEdgeTests(TransactionTestCase):
    def setUp(self):
        _enable_checkout()
        self.variant = _catalog_variant(sku="EDGE-STOCK-1", stock=1)

    def test_two_place_order_stock_one_second_fails(self):
        first = Client()
        second = Client()
        first.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        second.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        ok = first.post(reverse("commerce:checkout"), _checkout_payload())
        self.assertEqual(ok.status_code, 302)
        fail = second.post(reverse("commerce:checkout"), _checkout_payload())
        self.assertEqual(Order.objects.count(), 1)
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 0)
        self.assertNotEqual(fail.status_code, 500)

    def test_double_post_same_cart_one_order(self):
        self.client.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        payload = _checkout_payload()
        first = self.client.post(reverse("commerce:checkout"), payload)
        second = self.client.post(reverse("commerce:checkout"), payload)
        self.assertEqual(first.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.assertIn(second.status_code, (200, 302))

    def test_failed_stock_checkout_clamps_qty(self):
        roomy = _catalog_variant(sku="EDGE-CLAMP-1", stock=5)
        self.client.post(reverse("commerce:cart_add", args=[roomy.pk]), {"qty": 3})
        roomy.stock_quantity = 1
        roomy.save(update_fields=["stock_quantity"])
        response = self.client.post(reverse("commerce:checkout"), _checkout_payload())
        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.get(status=Cart.Status.OPEN)
        self.assertEqual(cart.items.get(product_variant=roomy).qty, 1)

    def test_get_checkout_disables_submit_when_out_of_stock(self):
        self.client.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        self.variant.stock_quantity = 0
        self.variant.save(update_fields=["stock_quantity"])
        response = self.client.get(reverse("commerce:checkout"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["checkout_blocked"])
        self.assertContains(response, "disabled")
        self.assertContains(response, "без залишку")


class PromoMaxUsesEdgeTests(TestCase):
    def setUp(self):
        _enable_checkout()
        self.variant = _catalog_variant(sku="EDGE-PROMO-1", stock=10)
        self.promo = PromoCode.objects.create(
            code="ONCE1",
            discount_type=PromoCode.DiscountType.PERCENT,
            discount_value=Decimal("10"),
            max_uses=1,
            used_count=0,
            is_active=True,
        )

    def _checkout_with_promo(self, client: Client):
        client.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        cart = Cart.objects.get(session_key=client.session.session_key, status=Cart.Status.OPEN)
        cart.promo_code = self.promo
        cart.save(update_fields=["promo_code", "updated_at"])
        return client.post(reverse("commerce:checkout"), _checkout_payload())

    def test_second_order_drops_exhausted_promo(self):
        first_client = Client()
        second_client = Client()
        first = self._checkout_with_promo(first_client)
        self.assertEqual(first.status_code, 302)
        second = self._checkout_with_promo(second_client)
        self.assertEqual(second.status_code, 302)
        orders = list(Order.objects.order_by("pk"))
        self.assertEqual(len(orders), 2)
        self.assertEqual(orders[0].promo_code_id, self.promo.pk)
        self.assertIsNone(orders[1].promo_code_id)
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)


class UnpaidCardTtlTests(TestCase):
    def setUp(self):
        self.variant = _catalog_variant(sku="EDGE-TTL-1", stock=3)
        self.order = Order.objects.create(
            full_name="Картка ТТЛ",
            phone="380501112233",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CARD_ONLINE,
            payment_status=Order.PaymentStatus.UNPAID,
            total=Decimal("200.00"),
        )
        OrderItem.objects.create(
            order=self.order,
            product_variant=self.variant,
            product_name=self.variant.product.name,
            sku=self.variant.sku,
            unit_price=Decimal("200.00"),
            qty=2,
            line_total=Decimal("400.00"),
        )
        self.variant.stock_quantity = 1
        self.variant.save(update_fields=["stock_quantity"])

    def test_command_cancels_after_61_minutes_and_restores_stock(self):
        Order.objects.filter(pk=self.order.pk).update(
            created_at=timezone.now() - timedelta(minutes=61),
        )
        call_command("cancel_stale_card_orders")
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertTrue(self.order.stock_restored)
        self.assertEqual(self.variant.stock_quantity, 3)

    def test_fresh_unpaid_card_is_kept(self):
        call_command("cancel_stale_card_orders")
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.NEW)


@override_settings(MONOBANK_TOKEN="test-token")
class MonobankCancelledWebhookTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.order = Order.objects.create(
            full_name="Тест",
            phone="380501112233",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CARD_ONLINE,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_intent_id="inv_cancel",
            total=Decimal("100.00"),
            status=Order.Status.CANCELLED,
        )
        Order.objects.filter(pk=self.order.pk).update(number="ORD-EDGE-1")
        self.order.refresh_from_db()

    @patch("src.commerce.views_1.get_monobank_service")
    def test_success_on_cancelled_does_not_mark_paid(self, mock_get):
        mono = MagicMock()
        mono.verify_webhook.return_value = True
        mock_get.return_value = mono
        payload = {
            "invoiceId": "inv_cancel",
            "status": "success",
            "reference": "ORD-EDGE-1",
            "modifiedDate": "2026-11-23T10:00:00Z",
        }
        response = self.client.post(
            reverse("commerce:payment_webhook"),
            data=json.dumps(payload).encode(),
            content_type="application/json",
            headers={"X-Sign": "dGVzdA=="},
        )
        self.assertEqual(response.status_code, 200)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, Order.PaymentStatus.UNPAID)
        self.assertEqual(self.order.status, Order.Status.CANCELLED)
        self.assertEqual(self.order.payment_idempotency_key, webhook_idempotency_key(payload))

    @patch("src.commerce.views_1.get_monobank_service")
    def test_expired_cancels_unpaid_and_restores_stock(self, mock_get):
        variant = _catalog_variant(sku="EDGE-WH-1", stock=1)
        live = Order.objects.create(
            full_name="Живе",
            phone="380501112233",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CARD_ONLINE,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_intent_id="inv_exp",
            total=Decimal("200.00"),
        )
        OrderItem.objects.create(
            order=live,
            product_variant=variant,
            product_name=variant.product.name,
            sku=variant.sku,
            unit_price=Decimal("200.00"),
            qty=1,
            line_total=Decimal("200.00"),
        )
        Order.objects.filter(pk=live.pk).update(number="ORD-EDGE-EXP")
        live.refresh_from_db()
        mono = MagicMock()
        mono.verify_webhook.return_value = True
        mock_get.return_value = mono
        payload = {
            "invoiceId": "inv_exp",
            "status": "expired",
            "reference": "ORD-EDGE-EXP",
        }
        response = self.client.post(
            reverse("commerce:payment_webhook"),
            data=json.dumps(payload).encode(),
            content_type="application/json",
            headers={"X-Sign": "dGVzdA=="},
        )
        self.assertEqual(response.status_code, 200)
        live.refresh_from_db()
        variant.refresh_from_db()
        self.assertEqual(live.status, Order.Status.CANCELLED)
        self.assertTrue(live.stock_restored)
        self.assertEqual(variant.stock_quantity, 2)

    @patch("src.commerce.views_1.get_monobank_service")
    def test_failure_does_not_cancel_unpaid_order(self, mock_get):
        live = Order.objects.create(
            full_name="Спроба",
            phone="380501112233",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CARD_ONLINE,
            payment_status=Order.PaymentStatus.UNPAID,
            payment_intent_id="inv_fail",
            total=Decimal("100.00"),
        )
        Order.objects.filter(pk=live.pk).update(number="ORD-EDGE-FAIL")
        live.refresh_from_db()
        mono = MagicMock()
        mono.verify_webhook.return_value = True
        mock_get.return_value = mono
        payload = {
            "invoiceId": "inv_fail",
            "status": "failure",
            "reference": "ORD-EDGE-FAIL",
        }
        response = self.client.post(
            reverse("commerce:payment_webhook"),
            data=json.dumps(payload).encode(),
            content_type="application/json",
            headers={"X-Sign": "dGVzdA=="},
        )
        self.assertEqual(response.status_code, 200)
        live.refresh_from_db()
        self.assertEqual(live.status, Order.Status.NEW)
        self.assertEqual(live.payment_status, Order.PaymentStatus.UNPAID)
        self.assertFalse(live.stock_restored)
