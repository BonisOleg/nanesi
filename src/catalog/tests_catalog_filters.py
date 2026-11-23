"""Каталог: порожні фільтри, сміття в GET, stock_only при sort/page."""
from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse

from src.catalog.models import Brand, Category, Product, ProductVariant
from src.catalog.selectors import parse_catalog_filters


class CatalogFilterEdgeTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="ФільтрБренд", slug="filter-brand")
        self.category = Category.objects.create(name="ФільтрКат", slug="filter-cat")
        self.product = Product.objects.create(
            name="Крем Фільтр",
            slug="krem-filter",
            brand=self.brand,
            category=self.category,
            is_active=True,
        )
        ProductVariant.objects.create(
            product=self.product,
            sku="FILTER-SKU-1",
            retail_price=Decimal("150.00"),
            stock_quantity=4,
            is_active=True,
        )
        self.url = reverse("catalog:catalog")
        self.category_url = self.category.get_absolute_url()

    def test_empty_filter_combo_returns_200_and_copy(self):
        response = self.client.get(self.url, {"sale": "1", "stock": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Нічого не знайдено")

    def test_invalid_price_min_ignored(self):
        response = self.client.get(self.url, {"price_min": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Крем Фільтр")
        self.assertEqual(response.context["price_min"], "")

    def test_invalid_sort_defaults_manual(self):
        response = self.client.get(self.url, {"sort": "drop_table"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "manual")
        self.assertContains(response, "Крем Фільтр")

    def test_page_beyond_last_still_shows_products(self):
        response = self.client.get(self.url, {"page": "99"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Крем Фільтр")
        self.assertEqual(response.context["page_obj"].number, 1)

    def test_negative_page_is_first(self):
        response = self.client.get(self.url, {"page": "-1"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)
        self.assertContains(response, "Крем Фільтр")

    def test_search_special_chars_ok(self):
        response = self.client.get(self.url, {"q": "%_"})
        self.assertEqual(response.status_code, 200)

    def test_query_truncated_to_200(self):
        factory = RequestFactory()
        request = factory.get("/katalog/", {"q": "я" * 250})
        filters = parse_catalog_filters(request)
        self.assertEqual(len(filters["query"]), 200)

    def test_sort_without_stock_keeps_in_stock_default(self):
        response = self.client.get(self.category_url, {"sort": "price-asc"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["stock_only"])

    def test_page_without_stock_keeps_in_stock_default(self):
        response = self.client.get(self.url, {"page": "1"})
        self.assertTrue(response.context["stock_only"])

    def test_brand_filter_without_stock_turns_stock_off(self):
        response = self.client.get(self.url, {"brand": "filter-brand"})
        self.assertFalse(response.context["stock_only"])

    def test_explicit_stock_one_stays_on(self):
        response = self.client.get(self.url, {"sort": "name", "stock": "1"})
        self.assertTrue(response.context["stock_only"])
