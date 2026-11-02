"""Адмінка товарів: українська мова, іконки, фільтри над таблицею."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Brand, Category, Product, ProductVariant
from src.core.middleware import AdminUkrainianLocaleMiddleware


class AdminUkrainianLocaleTests(TestCase):
    def test_public_ru_and_en_are_not_forced_to_uk(self):
        ru = self.client.get("/ru/", HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(ru.status_code, 200)
        self.assertContains(ru, 'lang="ru"')
        self.assertEqual(ru.headers["Content-Language"], "ru")

        en = self.client.get("/en/", HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(en.status_code, 200)
        self.assertContains(en, 'lang="en"')
        self.assertEqual(en.headers["Content-Language"], "en")

    def test_middleware_leaves_public_language(self):
        request = RequestFactory().get("/en/", HTTP_ACCEPT_LANGUAGE="en")
        translation.activate("en")
        request.LANGUAGE_CODE = "en"
        seen = {}

        def get_response(req):
            seen["language"] = translation.get_language()
            seen["code"] = req.LANGUAGE_CODE
            return HttpResponse("ok")

        AdminUkrainianLocaleMiddleware(get_response)(request)
        self.assertEqual(seen["language"], "en")
        self.assertEqual(seen["code"], "en")

    def test_middleware_activates_uk_for_admin_without_touching_cookie(self):
        request = RequestFactory().get(reverse("admin:index"), HTTP_ACCEPT_LANGUAGE="en")
        translation.activate("en")
        request.LANGUAGE_CODE = "en"
        seen = {}

        def get_response(req):
            seen["language"] = translation.get_language()
            seen["code"] = req.LANGUAGE_CODE
            response = HttpResponse("ok")
            return response

        response = AdminUkrainianLocaleMiddleware(get_response)(request)
        self.assertEqual(seen["language"], "uk")
        self.assertEqual(seen["code"], "uk")
        self.assertNotIn("django_language", response.cookies)


class ProductAdminUxTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser("adminux", "ux@example.com", "pass-word-1")
        self.client.force_login(self.user)
        self.brand = Brand.objects.create(name="Бренд UX", slug="brand-ux")
        self.category = Category.objects.create(name="Категорія UX", slug="cat-ux")
        self.product = Product.objects.create(
            name="Сироватка з дуже довгою назвою для переносу в списку",
            slug="serum-ux",
            brand=self.brand,
            category=self.category,
            is_active=True,
            is_hit=False,
            is_new=True,
            priority=3,
        )
        ProductVariant.objects.create(
            product=self.product,
            sku="UX-SKU-1",
            retail_price=Decimal("199.00"),
            stock_quantity=4,
            is_active=True,
        )

    def test_changelist_is_ukrainian_with_top_select_filters(self):
        self.client.cookies["django_language"] = "en"
        url = reverse("admin:catalog_product_changelist")
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for forbidden in (
            "Type to search",
            "Select action",
            "Filters",
            ">True<",
            ">False<",
            "By ",
        ):
            self.assertNotContains(response, forbidden)
        self.assertContains(response, "admin-top-filters")
        self.assertContains(response, "Усі")
        self.assertContains(response, "<select")
        for label in ("Активний", "Хіт", "Новинка", "Категорія", "Бренд"):
            self.assertIn(
                f'<span class="admin-top-filters__label">{label}</span>',
                html,
                msg=f"Немає верхнього фільтра «{label}»",
            )
        self.assertIn(">Усі</option>", html)
        self.assertIn(self.brand.name, html)
        self.assertIn(self.category.name, html)
        self.assertNotIn(
            '<span class="admin-top-filters__label">Постачальник</span>',
            html,
        )
        self.assertEqual(self.client.cookies["django_language"].value, "en")
        self.assertNotIn("changelist-filter", html)
        self.assertIn("admin/css/admin_changelist.css", html)
        self.assertRegex(
            html,
            r"admin-top-filters__select[\s\S]{0,400}appearance\s*:\s*none",
            msg="Верхні select-фільтри мають приховувати нативну стрілку (один шеврон Unfold)",
        )

        filtered = self.client.get(url + "?is_active__exact=1", HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(filtered.status_code, 200)
        self.assertContains(filtered, "selected")
        self.assertContains(filtered, "Так")

    def test_admin_jsi18n_is_ukrainian(self):
        url = reverse("admin:jsi18n")
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("%s selected option not visible", body)
        self.assertIn(
            r"%s \u043e\u0431\u0440\u0430\u043d\u0438\u0439 \u0432\u0430\u0440\u0456\u0430\u043d\u0442",
            body,
        )
        self.assertIn("(click to clear)", body)
        self.assertIn(r"(\u043d\u0430\u0442\u0438\u0441\u043d\u0456\u0442\u044c", body)

    def test_change_form_priority_help_is_ukrainian(self):
        url = reverse("admin:catalog_product_change", args=[self.product.pk])
        response = self.client.get(url, HTTP_ACCEPT_LANGUAGE="en")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Більше число — вище в списку. 0 — звичайний порядок")
        self.assertContains(response, "Пріоритет")
