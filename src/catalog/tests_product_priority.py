"""Пріоритет товару в каталозі: більше число вище лише в ручному порядку."""
import re
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from src.catalog.models import (
    Brand,
    Category,
    CategoryProductPosition,
    Product,
    ProductVariant,
    Review,
)
from src.catalog.selectors import SORT_OPTIONS


def _sort_label(value: str) -> str:
    for key, label in SORT_OPTIONS:
        if key == value:
            return str(label)
    raise AssertionError(f"немає sort={value} у SORT_OPTIONS")


def _product(brand, category, name, slug, *, price, priority=0, rating=None):
    product = Product.objects.create(
        name=name,
        slug=slug,
        brand=brand,
        category=category,
        is_active=True,
        priority=priority,
    )
    ProductVariant.objects.create(
        product=product,
        sku=slug,
        retail_price=price,
        stock_quantity=5,
        is_active=True,
    )
    if rating is not None:
        Review.objects.create(
            product=product,
            rating=rating,
            text="Відгук",
            is_approved=True,
        )
    return product


def _names(response) -> list[str]:
    return [item.name for item in response.context["products"]]


class ProductPriorityCatalogTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="ПріоритетБренд", slug="prio-brand")
        self.category = Category.objects.create(name="ПріоритетКатегорія", slug="prio-cat")
        self.boosted = _product(
            self.brand,
            self.category,
            "ПріоБуст",
            "prio-boost",
            price=Decimal("150.00"),
            priority=5,
            rating=2,
        )
        self.rated = _product(
            self.brand,
            self.category,
            "ПріоРейтинг",
            "prio-rated",
            price=Decimal("400.00"),
            priority=0,
            rating=5,
        )
        self.positioned = _product(
            self.brand,
            self.category,
            "ПріоПозиція",
            "prio-pos",
            price=Decimal("50.00"),
            priority=0,
            rating=1,
        )
        CategoryProductPosition.objects.create(
            category=self.category,
            product=self.positioned,
            position=0,
        )
        self.catalog_url = reverse("catalog:catalog")
        self.category_url = reverse(
            "catalog:category_detail",
            kwargs={"category_slug": self.category.slug},
        )

    def test_priority_raises_lower_rated_product_on_catalog(self):
        response = self.client.get(self.catalog_url)
        self.assertEqual(response.status_code, 200)
        names = _names(response)
        self.assertEqual(names[0], "ПріоБуст")
        self.assertEqual(Review.objects.get(product=self.boosted).rating, 2)
        self.assertEqual(Review.objects.get(product=self.rated).rating, 5)
        self.assertLess(names.index("ПріоБуст"), names.index("ПріоРейтинг"))

    def test_priority_raises_product_in_category_without_sort(self):
        response = self.client.get(self.category_url)
        self.assertEqual(response.status_code, 200)
        names = _names(response)
        self.assertLess(names.index("ПріоБуст"), names.index("ПріоРейтинг"))

    def test_category_position_beats_priority(self):
        response = self.client.get(self.category_url)
        names = _names(response)
        self.assertLess(names.index("ПріоПозиція"), names.index("ПріоБуст"))
        self.assertGreater(self.boosted.priority, self.positioned.priority)

    def test_price_desc_ignores_priority(self):
        response = self.client.get(self.catalog_url, {"sort": "price-desc"})
        self.assertEqual(
            _names(response),
            ["ПріоРейтинг", "ПріоБуст", "ПріоПозиція"],
        )
        self.assertGreater(self.boosted.priority, self.rated.priority)

    def test_catalog_without_sort_selects_manual(self):
        response = self.client.get(self.catalog_url)
        self.assertEqual(response.context["sort"], "manual")
        html = response.content.decode()
        label = _sort_label("manual")
        self.assertEqual(label, "Ручний порядок")
        self.assertIn(f'<option value="manual" selected>{label}</option>', html)
        self.assertEqual(len(re.findall(r"<option\b[^>]*\sselected\b", html)), 1)
        self.assertRegex(
            html,
            rf'id="catalog-sort-current"[^>]*data-catalog-sort-current[^>]*>\s*{re.escape(label)}\s*</span>',
        )

    def test_price_desc_selects_option_and_current_label(self):
        response = self.client.get(self.catalog_url, {"sort": "price-desc"})
        self.assertEqual(response.context["sort"], "price-desc")
        html = response.content.decode()
        label = _sort_label("price-desc")
        self.assertEqual(label, "Ціна: спадання")
        self.assertIn(f'<option value="price-desc" selected>{label}</option>', html)
        self.assertRegex(
            html,
            rf'data-catalog-sort-current[^>]*>\s*{re.escape(label)}\s*</span>',
        )
