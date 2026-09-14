"""Кабінет покупця: реєстрація, профіль, обране, замовлення, НП, гість-checkout."""
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from src.accounts.models import User, Wishlist
from src.catalog.models import Brand, Category, Product, ProductVariant
from src.commerce.models import Cart, Order
from src.content.models import SiteSettings


class CabinetFixturesMixin:
    password = "NanesiCab1"

    def setUp(self):
        site = SiteSettings.load()
        site.nova_poshta_enabled = True
        site.ukrposhta_enabled = True
        site.cash_on_delivery_enabled = True
        site.card_payment_enabled = False
        site.save(update_fields=[
            "nova_poshta_enabled", "ukrposhta_enabled",
            "cash_on_delivery_enabled", "card_payment_enabled",
        ])
        brand = Brand.objects.create(name="CabBrand", slug="cab-brand")
        category = Category.objects.create(name="CabCat", slug="cab-cat")
        self.product = Product.objects.create(
            name="Serum Cab", slug="serum-cab", brand=brand, category=category, is_active=True,
        )
        self.product_b = Product.objects.create(
            name="Cream Cab", slug="cream-cab", brand=brand, category=category, is_active=True,
        )
        self.variant = ProductVariant.objects.create(
            product=self.product, sku="CAB-SKU-1", retail_price=Decimal("200.00"),
            stock_quantity=10, is_active=True,
        )
        ProductVariant.objects.create(
            product=self.product_b, sku="CAB-SKU-2", retail_price=Decimal("300.00"),
            stock_quantity=10, is_active=True,
        )

    def _np_checkout(self, extra=None):
        data = {
            "full_name": "Тест Кабінет",
            "phone": "380501112233",
            "email": "guest-cab@test.test",
            "delivery_method": "np_warehouse",
            "np_city_name": "Київ",
            "np_city_ref": "city-ref",
            "np_warehouse_name": "Відділення 1",
            "np_warehouse_ref": "wh-ref",
            "payment_method": "cod",
            "privacy_consent": "on",
        }
        if extra:
            data.update(extra)
        return data


class RegisterLoginProfileTests(CabinetFixturesMixin, TestCase):
    def test_register_and_login_by_email(self):
        response = self.client.post(reverse("accounts:login"), {
            "form": "register",
            "full_name": "Оля Тест",
            "email": "olya.cab@test.test",
            "password1": self.password,
            "password2": self.password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(email="olya.cab@test.test").exists())
        self.client.logout()
        response = self.client.post(reverse("accounts:login"), {
            "form": "login",
            "username": "olya.cab@test.test",
            "password": self.password,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:profile"))

    def test_profile_update(self):
        user = User.objects.create_user(
            username="cab1", email="cab1@test.test", password=self.password, first_name="Оля",
        )
        self.client.force_login(user)
        response = self.client.post(reverse("accounts:profile"), {
            "form": "profile",
            "first_name": "Олена",
            "last_name": "Тест",
            "email": "cab1@test.test",
            "phone": "380671112233",
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.first_name, "Олена")
        self.assertEqual(user.phone, "380671112233")


class WishlistMergeTests(CabinetFixturesMixin, TestCase):
    def test_toggle_and_merge_guest_ids_on_register(self):
        response = self.client.post(reverse("accounts:login"), {
            "form": "register",
            "full_name": "Гість",
            "email": "wish.merge@test.test",
            "password1": self.password,
            "password2": self.password,
            "wishlist_ids": f"{self.product.pk},{self.product_b.pk}",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="wish.merge@test.test")
        ids = set(Wishlist.objects.filter(user=user).values_list("product_id", flat=True))
        self.assertEqual(ids, {self.product.pk, self.product_b.pk})

        self.client.post(reverse("accounts:wishlist_toggle", args=[self.product.pk]))
        self.assertFalse(Wishlist.objects.filter(user=user, product=self.product).exists())

    def test_guest_wishlist_render(self):
        response = self.client.get(
            reverse("accounts:wishlist_render"),
            {"ids": f"{self.product.pk}"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Serum Cab")


class OrdersAndRepeatTests(CabinetFixturesMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            username="buyer", email="buyer.cab@test.test", password=self.password,
        )

    def test_orders_require_login(self):
        response = self.client.get(reverse("accounts:order_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/kabinet/vkhid/", response.url)

    def test_history_detail_and_repeat(self):
        self.client.force_login(self.user)
        self.client.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 2})
        response = self.client.post(reverse("commerce:checkout"), self._np_checkout())
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(user=self.user)
        self.assertIsNotNone(order.number)

        list_resp = self.client.get(reverse("accounts:order_list"))
        self.assertContains(list_resp, order.number)

        detail = self.client.get(reverse("accounts:order_detail", args=[order.number]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "Повторити замовлення")

        repeat = self.client.post(reverse("accounts:order_repeat", args=[order.number]))
        self.assertEqual(repeat.status_code, 302)
        self.assertEqual(repeat.url, reverse("commerce:cart"))
        cart = Cart.objects.filter(user=self.user, status=Cart.Status.OPEN).first()
        self.assertIsNotNone(cart)
        self.assertEqual(cart.items.get(product_variant=self.variant).qty, 2)


class SavedNovaPoshtaTests(CabinetFixturesMixin, TestCase):
    def test_profile_saves_city_and_warehouse(self):
        user = User.objects.create_user(
            username="npuser", email="np@test.test", password=self.password,
        )
        self.client.force_login(user)
        response = self.client.post(reverse("accounts:profile"), {
            "form": "warehouse",
            "saved_np_city_name": "Львів",
            "saved_np_city_ref": "lviv-ref",
            "saved_np_warehouse_name": "Поштомат 12",
            "saved_np_warehouse_ref": "pm-ref",
        })
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertEqual(user.saved_np_city_name, "Львів")
        self.assertEqual(user.saved_np_warehouse_ref, "pm-ref")

        self.client.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        checkout = self.client.get(reverse("commerce:checkout"))
        self.assertContains(checkout, "Львів")
        self.assertContains(checkout, "Поштомат 12")

    def test_checkout_persists_np_for_auth_user(self):
        user = User.objects.create_user(
            username="np2", email="np2@test.test", password=self.password,
        )
        self.client.force_login(user)
        self.client.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        self.client.post(reverse("commerce:checkout"), self._np_checkout())
        user.refresh_from_db()
        self.assertEqual(user.saved_np_city_ref, "city-ref")
        self.assertEqual(user.saved_np_warehouse_ref, "wh-ref")


class GuestCheckoutTests(CabinetFixturesMixin, TestCase):
    def test_checkout_without_registration(self):
        self.client.post(reverse("commerce:cart_add", args=[self.variant.pk]), {"qty": 1})
        get_resp = self.client.get(reverse("commerce:checkout"))
        self.assertEqual(get_resp.status_code, 200)
        post = self.client.post(reverse("commerce:checkout"), self._np_checkout())
        self.assertEqual(post.status_code, 302)
        order = Order.objects.get()
        self.assertIsNone(order.user)
        self.assertTrue(post.url.endswith(f"/dyakuyemo/{order.number}/"))
        thanks = self.client.get(reverse("commerce:thank_you", args=[order.number]))
        self.assertEqual(thanks.status_code, 200)
