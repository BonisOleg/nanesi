from decimal import Decimal

from django.test import TestCase

from src.commerce.models import Order
from src.commerce.selectors import format_uah_amount, free_shipping_progress
from src.content.models import SiteSettings


class FreeShippingProgressTests(TestCase):
    def setUp(self):
        site = SiteSettings.load()
        site.free_shipping_threshold = Decimal("1500.00")
        site.save(update_fields=["free_shipping_threshold"])

    def test_remaining_copy_values(self):
        progress = free_shipping_progress(Decimal("1200.00"))
        self.assertFalse(progress.reached)
        self.assertEqual(progress.remaining_display, "300")
        self.assertEqual(progress.percent, 80)

    def test_reached_at_threshold(self):
        progress = free_shipping_progress(Decimal("1500.00"))
        self.assertTrue(progress.reached)
        self.assertEqual(progress.percent, 100)
        self.assertEqual(progress.remaining_display, "0")

    def test_disabled_when_threshold_empty(self):
        site = SiteSettings.load()
        site.free_shipping_threshold = None
        site.save(update_fields=["free_shipping_threshold"])
        progress = free_shipping_progress(Decimal("2000.00"))
        self.assertIsNone(progress.threshold)
        self.assertFalse(progress.reached)

    def test_format_uah_amount(self):
        self.assertEqual(format_uah_amount(Decimal("300.00")), "300")
        self.assertEqual(format_uah_amount(Decimal("300.50")), "300,50")

    def test_promo_does_not_undo_free_shipping_progress(self):
        """Пороги рахуються від subtotal; знижка 1589→1430 не знімає reached."""
        progress = free_shipping_progress(Decimal("1589.00"))
        self.assertTrue(progress.reached)
        self.assertEqual(progress.percent, 100)


class PromoDiscountMoneyTests(TestCase):
    def test_percent_discount_two_decimals(self):
        from src.commerce.models import PromoCode

        promo = PromoCode(
            code="TEST10",
            discount_type=PromoCode.DiscountType.PERCENT,
            discount_value=Decimal("10"),
            is_active=True,
        )
        discount = promo.calculate_discount(Decimal("1589.00"))
        self.assertEqual(discount, Decimal("158.90"))
        self.assertEqual(str(discount), "158.90")
        total = Decimal("1589.00") - discount
        from src.commerce.models_1 import money

        self.assertEqual(money(total), Decimal("1430.10"))
        self.assertEqual(str(money(total)), "1430.10")


class DeliveryMethodsTests(TestCase):
    def setUp(self):
        site = SiteSettings.load()
        site.nova_poshta_enabled = True
        site.ukrposhta_enabled = True
        site.save(update_fields=["nova_poshta_enabled", "ukrposhta_enabled"])

    def test_checkout_methods_np_and_ukrposhta_without_courier(self):
        from src.commerce.selectors import available_delivery_methods

        keys = [key for key, _label in available_delivery_methods()]
        self.assertEqual(keys, ["np_warehouse", "ukrposhta"])

    def test_form_rejects_courier(self):
        from src.commerce.forms import CheckoutForm

        form = CheckoutForm(data={
            "full_name": "Тест Тестенко",
            "phone": "380501112233",
            "delivery_method": "np_courier",
            "payment_method": "cod",
            "np_city_name": "Київ",
            "privacy_consent": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("delivery_method", form.errors)

    def test_form_requires_np_point(self):
        from src.commerce.forms import CheckoutForm

        form = CheckoutForm(data={
            "full_name": "Тест Тестенко",
            "phone": "380501112233",
            "delivery_method": "np_warehouse",
            "payment_method": "cod",
            "np_city_name": "Київ",
            "privacy_consent": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("np_warehouse_name", form.errors)

    def test_form_requires_ukrposhta_index(self):
        from src.commerce.forms import CheckoutForm

        form = CheckoutForm(data={
            "full_name": "Тест Тестенко",
            "phone": "380501112233",
            "delivery_method": "ukrposhta",
            "payment_method": "cod",
            "ukrposhta_address": "вул. Хрещатик, 1",
            "ukrposhta_index": "123",
            "privacy_consent": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("ukrposhta_index", form.errors)

        form_ok = CheckoutForm(data={
            "full_name": "Тест Тестенко",
            "phone": "380501112233",
            "delivery_method": "ukrposhta",
            "payment_method": "cod",
            "ukrposhta_address": "вул. Хрещатик, 1",
            "ukrposhta_index": "01001",
            "privacy_consent": True,
        })
        self.assertTrue(form_ok.is_valid())

    def test_form_requires_privacy_consent(self):
        from src.commerce.forms import CheckoutForm

        form = CheckoutForm(data={
            "full_name": "Тест Тестенко",
            "phone": "380501112233",
            "delivery_method": "ukrposhta",
            "payment_method": "cod",
            "ukrposhta_address": "вул. Хрещатик, 1",
            "ukrposhta_index": "01001",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("privacy_consent", form.errors)

    def test_persist_np_and_ukrposhta_separately(self):
        from django.contrib.auth import get_user_model

        from src.commerce.models import Order
        from src.commerce.services import persist_saved_delivery

        user = get_user_model().objects.create_user(username="buyer", password="x")
        persist_saved_delivery(user, {
            "delivery_method": Order.DeliveryMethod.NOVA_POSHTA_WAREHOUSE,
            "np_city_name": "Київ",
            "np_city_ref": "city-ref",
            "np_warehouse_name": "Поштомат · Хрещатик",
            "np_warehouse_ref": "wh-ref",
        })
        user.refresh_from_db()
        self.assertEqual(user.saved_np_warehouse_ref, "wh-ref")
        persist_saved_delivery(user, {
            "delivery_method": Order.DeliveryMethod.UKRPOSHTA,
            "ukrposhta_index": "01001",
            "ukrposhta_address": "Відділення 1, вул. Хрещатик, 1",
        })
        user.refresh_from_db()
        self.assertEqual(user.saved_ukrposhta_index, "01001")
        self.assertEqual(user.saved_ukrposhta_address, "Відділення 1, вул. Хрещатик, 1")
        self.assertEqual(user.saved_np_warehouse_ref, "wh-ref")


class CancelOrderRestoresStockTests(TestCase):
    def setUp(self):
        from src.accounts.models import User
        from src.catalog.models import Brand, Category, Product, ProductVariant
        from src.commerce.models import OrderItem

        self.user = User.objects.create_superuser(
            username="admin_stock", email="admin_stock@test.test", password="x",
        )
        brand = Brand.objects.create(name="TestBrand", slug="test-brand-stock")
        category = Category.objects.create(name="TestCat", slug="test-cat-stock")
        product = Product.objects.create(
            name="Toner", slug="toner-stock-test", brand=brand, category=category,
        )
        self.variant = ProductVariant.objects.create(
            product=product, sku="SKU-STOCK-1", retail_price=Decimal("100.00"), stock_quantity=0,
        )
        self.order = Order.objects.create(
            full_name="Тест",
            phone="380501112233",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CASH_ON_DELIVERY,
            status=Order.Status.NEW,
            total=Decimal("100.00"),
        )
        OrderItem.objects.create(
            order=self.order,
            product_variant=self.variant,
            product_name=product.name,
            sku=self.variant.sku,
            unit_price=Decimal("100.00"),
            qty=2,
            line_total=Decimal("200.00"),
        )

    def test_cancel_restores_stock_once(self):
        from src.commerce.services import change_order_status, restore_order_stock

        change_order_status(self.order, Order.Status.CANCELLED, user=self.user)
        self.variant.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 2)
        self.assertTrue(self.order.stock_restored)
        self.assertFalse(restore_order_stock(self.order))
        self.variant.refresh_from_db()
        self.assertEqual(self.variant.stock_quantity, 2)


class ChangeUnpaidCardPaymentTests(TestCase):
    def setUp(self):
        site = SiteSettings.load()
        site.cash_on_delivery_enabled = True
        site.bank_transfer_enabled = True
        site.save(update_fields=["cash_on_delivery_enabled", "bank_transfer_enabled"])
        self.order = Order.objects.create(
            full_name="Тест",
            phone="+380501112233",
            delivery_method=Order.DeliveryMethod.UKRPOSHTA,
            ukrposhta_index="01001",
            ukrposhta_address="Київ",
            payment_method=Order.PaymentMethod.CARD_ONLINE,
            payment_status=Order.PaymentStatus.UNPAID,
            total=Decimal("100.00"),
        )

    def test_switch_to_cod(self):
        from src.commerce.services import change_unpaid_card_payment_method

        change_unpaid_card_payment_method(self.order, Order.PaymentMethod.CASH_ON_DELIVERY)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.CASH_ON_DELIVERY)

    def test_rejects_paid_order(self):
        from src.commerce.services import PaymentMethodError, change_unpaid_card_payment_method

        self.order.payment_status = Order.PaymentStatus.PAID
        self.order.save(update_fields=["payment_status"])
        with self.assertRaises(PaymentMethodError):
            change_unpaid_card_payment_method(self.order, Order.PaymentMethod.CASH_ON_DELIVERY)

    def test_thank_you_shows_pending_and_switch(self):
        session = self.client.session
        session["last_order_number"] = self.order.number
        session.save()
        response = self.client.get(f"/dyakuyemo/{self.order.number}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Оплата не пройшла")
        self.assertContains(response, 'name="payment_method"')
        self.assertContains(response, "purchase")

    def test_thank_you_post_switches_method(self):
        session = self.client.session
        session["last_order_number"] = self.order.number
        session.save()
        response = self.client.post(
            f"/dyakuyemo/{self.order.number}/",
            {"action": "change_payment", "payment_method": Order.PaymentMethod.BANK_TRANSFER},
        )
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_method, Order.PaymentMethod.BANK_TRANSFER)


class PromoApplyHxFeedbackTests(TestCase):
    def test_exhausted_promo_inline_not_in_session_messages(self):
        from django.contrib.messages import get_messages

        from src.commerce.models import PromoCode

        PromoCode.objects.create(
            code="USEDUP",
            discount_type=PromoCode.DiscountType.PERCENT,
            discount_value=Decimal("10"),
            max_uses=1,
            used_count=1,
            is_active=True,
        )
        self.client.get("/koshyk/")
        response = self.client.post(
            "/koshyk/promo/apply/",
            {"code": "USEDUP"},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "вичерпано")
        self.assertEqual(len(list(get_messages(response.wsgi_request))), 0)


class CartDrawerAndContactsTests(TestCase):
    def setUp(self):
        from src.catalog.models import Brand, Category, Product, ProductVariant
        from src.content.models import SiteSettings

        site = SiteSettings.load()
        site.nova_poshta_enabled = True
        site.cash_on_delivery_enabled = True
        site.save(update_fields=["nova_poshta_enabled", "cash_on_delivery_enabled"])

        brand = Brand.objects.create(name="CartBrand", slug="cart-brand")
        category = Category.objects.create(name="CartCat", slug="cart-cat")
        product = Product.objects.create(
            name="Serum", slug="serum-cart", brand=brand, category=category, is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product, sku="SKU-CART-1", retail_price=Decimal("200.00"),
            stock_quantity=5, is_active=True,
        )

    def test_summary_fragment_ok(self):
        response = self.client.get("/koshyk/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Кошик порожній")

    def test_checkout_post_saves_contacts_even_if_invalid(self):
        from src.commerce.models import Cart

        self.client.post(
            f"/koshyk/add/{self.variant.pk}/",
            {"qty": 1, "ajax": "1"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="fetch",
        )
        response = self.client.post("/oformlennya/", {
            "full_name": "Іван Тест",
            "phone": "380501112233",
            "email": "ivan@test.test",
            "delivery_method": "np_warehouse",
            "payment_method": "cod",
            # без міста/відділення і без privacy — форма невалідна
        })
        self.assertEqual(response.status_code, 200)
        cart = Cart.objects.filter(status=Cart.Status.OPEN).order_by("-updated_at").first()
        self.assertIsNotNone(cart)
        self.assertEqual(cart.contact_full_name, "Іван Тест")
        self.assertEqual(cart.contact_phone, "380501112233")
        self.assertEqual(cart.contact_email, "ivan@test.test")

    def test_save_cart_contacts_service(self):
        from django.contrib.auth.models import AnonymousUser
        from django.test import RequestFactory

        from src.commerce.models import Cart
        from src.commerce.services import save_cart_contacts

        self.client.post(
            f"/koshyk/add/{self.variant.pk}/",
            {"qty": 1, "ajax": "1"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="fetch",
        )
        factory = RequestFactory()
        request = factory.post("/oformlennya/")
        request.session = self.client.session
        request.user = AnonymousUser()
        cart = save_cart_contacts(
            request, full_name="Аня", phone="380671112233", email="a@test.test",
        )
        cart.refresh_from_db()
        self.assertEqual(cart.contact_full_name, "Аня")
        self.assertEqual(Cart.objects.get(pk=cart.pk).contact_phone, "380671112233")
        self.assertEqual(cart.contact_email, "a@test.test")

