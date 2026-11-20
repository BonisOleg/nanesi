from decimal import Decimal

from django.test import TestCase

from src.catalog.models import Brand, Category, Product, ProductVariant
from src.commerce.models import Order, OrderItem


class ThankYouPurchaseTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="SKIN1004", slug="skin1004-purchase")
        category = Category.objects.create(name="Догляд за обличчям", slug="doglyad-za-oblychchyam")
        product = Product.objects.create(
            name="Ампула", slug="ampula-purchase", brand=brand, category=category, is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product,
            sku="SKIN1004_AMP_10",
            retail_price=Decimal("990.00"),
            stock_quantity=5,
            is_active=True,
        )
        self.order = Order.objects.create(
            full_name="Олена Тест",
            phone="0991234567",
            email="customer@example.com",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CASH_ON_DELIVERY,
            payment_status=Order.PaymentStatus.UNPAID,
            total=Decimal("990.00"),
            shipping_cost=Decimal("0"),
        )
        OrderItem.objects.create(
            order=self.order,
            product_variant=self.variant,
            product_name=product.name,
            sku=self.variant.sku,
            unit_price=Decimal("990.00"),
            qty=1,
            line_total=Decimal("990.00"),
        )

    def _open_thanks(self, order):
        session = self.client.session
        session["last_order_number"] = order.number
        session.save()
        return self.client.get(f"/dyakuyemo/{order.number}/")

    def test_cod_sends_purchase_with_user_data(self):
        response = self._open_thanks(self.order)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"event": "purchase"')
        self.assertContains(response, '"item_id": "SKIN1004_AMP_10"')
        self.assertContains(response, '"item_brand": "SKIN1004"')
        self.assertContains(response, '"item_category": "Догляд за обличчям"')
        self.assertContains(response, '"email": "customer@example.com"')
        self.assertContains(response, '"phone_number": "+380991234567"')
        self.assertContains(response, '"transaction_id":')
        self.assertContains(response, '"value": 990.0')

    def test_unpaid_card_has_no_purchase(self):
        self.order.payment_method = Order.PaymentMethod.CARD_ONLINE
        self.order.save(update_fields=["payment_method"])
        response = self._open_thanks(self.order)
        self.assertNotContains(response, '"event": "purchase"')
        poll = self.client.get(f"/dyakuyemo/{self.order.number}/purchase/")
        self.assertEqual(poll.status_code, 200)
        self.assertContains(poll, "hx-get")
        self.assertNotContains(poll, '"event": "purchase"')

    def test_paid_card_sends_purchase(self):
        self.order.payment_method = Order.PaymentMethod.CARD_ONLINE
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_method", "payment_status"])
        response = self._open_thanks(self.order)
        self.assertContains(response, '"event": "purchase"')
        self.assertNotContains(response, 'id="purchase-poll"')

    def test_paid_card_poll_stops_and_emits_event(self):
        self.order.payment_method = Order.PaymentMethod.CARD_ONLINE
        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_method", "payment_status"])
        session = self.client.session
        session["last_order_number"] = self.order.number
        session.save()
        poll = self.client.get(f"/dyakuyemo/{self.order.number}/purchase/")
        self.assertContains(poll, '"event": "purchase"')
        self.assertNotContains(poll, "hx-get")
