"""Валідація вводу, honeypot, brute-force, open redirect, CSRF."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from src.accounts.models import User
from src.catalog.models import Brand, Category, Product, ProductVariant
from src.commerce.forms import CheckoutForm
from src.commerce.models import Cart, Order
from src.content.models import NewsletterLead, SiteSettings
from src.core.analytics import events_json
from src.core.validators import normalize_ua_phone, validate_person_name


class PhoneNormalizeTests(TestCase):
    def test_plus380_spaces_and_dashes(self):
        self.assertEqual(normalize_ua_phone("+380 67 111-22-33"), "380671112233")

    def test_national_zero(self):
        self.assertEqual(normalize_ua_phone("0671112233"), "380671112233")

    def test_stored_format(self):
        self.assertEqual(normalize_ua_phone("380671112233"), "380671112233")

    def test_nine_digits(self):
        self.assertEqual(normalize_ua_phone("671112233"), "380671112233")

    def test_garbage_rejected(self):
        with self.assertRaises(ValidationError):
            normalize_ua_phone("not-a-phone")
        with self.assertRaises(ValidationError):
            normalize_ua_phone("12345")


class PersonNameTests(TestCase):
    def test_ukrainian_hyphen_and_apostrophe(self):
        self.assertEqual(validate_person_name("Марія-Анна"), "Марія-Анна")
        self.assertEqual(validate_person_name("О'Коннор"), "О'Коннор")

    def test_digits_and_html_rejected(self):
        with self.assertRaises(ValidationError):
            validate_person_name("Іван123")
        with self.assertRaises(ValidationError):
            validate_person_name("<script>alert(1)</script>")


class CheckoutValidationTests(TestCase):
    def setUp(self):
        site = SiteSettings.load()
        site.nova_poshta_enabled = True
        site.cash_on_delivery_enabled = True
        site.card_payment_enabled = False
        site.save()

    def test_comment_max_length(self):
        form = CheckoutForm(data={
            "full_name": "Іван Тест",
            "phone": "+380501112233",
            "delivery_method": "np_warehouse",
            "np_city_name": "Київ",
            "np_warehouse_name": "Відділення 1",
            "payment_method": "cod",
            "privacy_consent": "on",
            "comment": "x" * 1001,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("comment", form.errors)

    def test_phone_normalized(self):
        form = CheckoutForm(data={
            "full_name": "Іван Тест",
            "phone": "0501112233",
            "delivery_method": "np_warehouse",
            "np_city_name": "Київ",
            "np_warehouse_name": "Відділення 1",
            "payment_method": "cod",
            "privacy_consent": "on",
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["phone"], "380501112233")


class HoneypotTests(TestCase):
    password = "NanesiCab1"

    def setUp(self):
        site = SiteSettings.load()
        site.nova_poshta_enabled = True
        site.cash_on_delivery_enabled = True
        site.card_payment_enabled = False
        site.save()
        brand = Brand.objects.create(name="SecBrand", slug="sec-brand")
        category = Category.objects.create(name="SecCat", slug="sec-cat")
        product = Product.objects.create(
            name="Serum Sec", slug="serum-sec", brand=brand, category=category, is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product, sku="SEC-SKU-1", retail_price=Decimal("200.00"),
            stock_quantity=10, is_active=True,
        )

    def test_register_honeypot_creates_no_user(self):
        response = self.client.post(reverse("accounts:login"), {
            "form": "register",
            "full_name": "Богдан Тест",
            "email": "honeypot.reg@test.test",
            "password1": self.password,
            "password2": self.password,
            "website": "http://spam.example",
        })
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(email="honeypot.reg@test.test").exists())

    def test_newsletter_honeypot_creates_no_lead(self):
        response = self.client.post(reverse("content:newsletter_subscribe"), {
            "email": "honeypot.news@test.test",
            "source": "popup",
            "website": "http://spam.example",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(NewsletterLead.objects.filter(email="honeypot.news@test.test").exists())

    def test_checkout_honeypot_creates_no_order(self):
        self.client.post(
            f"/koshyk/add/{self.variant.pk}/",
            {"qty": 1, "ajax": "1"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="fetch",
        )
        response = self.client.post("/oformlennya/", {
            "full_name": "Іван Тест",
            "phone": "380501112233",
            "email": "ivan.hp@test.test",
            "delivery_method": "np_warehouse",
            "np_city_name": "Київ",
            "np_city_ref": "city-ref",
            "np_warehouse_name": "Відділення 1",
            "np_warehouse_ref": "wh-ref",
            "payment_method": "cod",
            "privacy_consent": "on",
            "website": "http://spam.example",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)


class AuthSecurityTests(TestCase):
    password = "NanesiCab1"

    def test_open_redirect_on_register_rejected(self):
        response = self.client.post(reverse("accounts:login"), {
            "form": "register",
            "full_name": "Оля Тест",
            "email": "redirect.cab@test.test",
            "password1": self.password,
            "password2": self.password,
            "next": "https://evil.example/phish",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:profile"))
        self.assertNotIn("evil.example", response.url)

    def test_login_without_csrf_rejected(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(reverse("accounts:login"), {
            "form": "login",
            "username": "nobody@test.test",
            "password": "x",
        })
        self.assertEqual(response.status_code, 403)


@override_settings(AXES_ENABLED=True)
class AxesLockoutTests(TestCase):
    password = "NanesiCab1"

    def setUp(self):
        User.objects.create_user(
            username="axes-user", email="axes.lock@test.test", password=self.password,
        )

    def test_sixth_failed_login_locked(self):
        url = reverse("accounts:login")
        bad = {"form": "login", "username": "axes.lock@test.test", "password": "wrong-pass"}
        for _ in range(5):
            self.client.post(url, bad)
        locked = self.client.post(url, bad)
        self.assertEqual(locked.status_code, 429)
        good = self.client.post(url, {
            "form": "login",
            "username": "axes.lock@test.test",
            "password": self.password,
        })
        self.assertNotEqual(good.status_code, 302)

    def test_lockout_does_not_block_other_username_on_same_ip(self):
        User.objects.create_user(
            username="axes-other", email="axes.ok@test.test", password=self.password,
        )
        url = reverse("accounts:login")
        bad = {"form": "login", "username": "axes.lock@test.test", "password": "wrong-pass"}
        for _ in range(6):
            self.client.post(url, bad)
        ok = self.client.post(url, {
            "form": "login",
            "username": "axes.ok@test.test",
            "password": self.password,
        })
        self.assertEqual(ok.status_code, 302)


class JsonEscapeTests(TestCase):
    def test_events_json_escapes_script_breakout(self):
        payload = events_json({"event": "view_item", "name": "</script><img src=x>"})
        self.assertNotIn("</script>", payload)
        self.assertIn("\\u003c", payload)


class CartQtyTests(TestCase):
    def setUp(self):
        SiteSettings.load()
        brand = Brand.objects.create(name="QtyBrand", slug="qty-brand")
        category = Category.objects.create(name="QtyCat", slug="qty-cat")
        product = Product.objects.create(
            name="Qty Serum", slug="qty-serum", brand=brand, category=category, is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=product, sku="QTY-1", retail_price=Decimal("100.00"),
            stock_quantity=5, is_active=True,
        )

    def test_non_int_qty_returns_400(self):
        response = self.client.post(
            f"/koshyk/add/{self.variant.pk}/",
            {"qty": "abc", "ajax": "1"},
            HTTP_ACCEPT="application/json",
            HTTP_X_REQUESTED_WITH="fetch",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Cart.objects.count(), 0)
