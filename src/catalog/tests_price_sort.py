"""Сортування категорії за ціною разом із уже застосованими фільтрами."""
import re
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from src.catalog.models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Product,
    ProductVariant,
)


def _product(brand, category, name, slug, price, *, stock=5, created_at=None):
    product = Product.objects.create(
        name=name,
        slug=slug,
        brand=brand,
        category=category,
        is_active=True,
    )
    ProductVariant.objects.create(
        product=product,
        sku=slug,
        retail_price=price,
        stock_quantity=stock,
        is_active=True,
    )
    if created_at is not None:
        Product.objects.filter(pk=product.pk).update(created_at=created_at)
    return product


class CategoryPriceSortTests(TestCase):
    def setUp(self):
        self.kept = Brand.objects.create(name="Бренд Сорт", slug="sort-kept")
        self.other = Brand.objects.create(name="Інший Сорт", slug="sort-other")
        self.category = Category.objects.create(name="Догляд сортування", slug="sort-price-cat")
        skin = Attribute.objects.create(code="skin_type", name="Тип шкіри", is_filterable=True)
        self.dry = AttributeValue.objects.create(attribute=skin, value="Суха", slug="sukha-sort")
        oily = AttributeValue.objects.create(attribute=skin, value="Жирна", slug="zhyrna-sort")

        now = timezone.now()
        self.high = _product(
            self.kept, self.category, "БетаКрем", "beta-krem-sort", Decimal("500.00"),
            created_at=now - timedelta(days=3),
        )
        self.low = _product(
            self.kept, self.category, "АльфаКрем", "alfa-krem-sort", Decimal("100.00"),
            created_at=now - timedelta(days=2),
        )
        self.mid = _product(
            self.kept, self.category, "ГаммаКрем", "gamma-krem-sort", Decimal("200.00"),
            created_at=now - timedelta(days=1),
        )
        self.out_of_stock = _product(
            self.kept, self.category, "ЕпсилонКрем", "epsilon-krem-sort", Decimal("10.00"),
            stock=0,
        )
        self.other_brand = _product(
            self.other, self.category, "ДельтаКрем", "delta-krem-sort", Decimal("900.00"),
        )
        self.other_attr = _product(
            self.kept, self.category, "ЗетаКрем", "zeta-krem-sort", Decimal("800.00"),
        )
        for product in (self.high, self.low, self.mid, self.out_of_stock, self.other_brand):
            product.attribute_values.add(self.dry)
        self.other_attr.attribute_values.add(oily)

    def test_price_desc_keeps_filters_and_selected_option(self):
        response = self.client.get(
            self.category.get_absolute_url(),
            {
                "brand": "sort-kept",
                "skin_type": "sukha-sort",
                "stock": "1",
                "sort": "price-desc",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "price-desc")
        self.assertEqual(
            [item.name for item in response.context["products"]],
            ["БетаКрем", "ГаммаКрем", "АльфаКрем"],
        )
        self.assertIn("sort-kept", response.context["selected_brands"])
        self.assertNotIn("sort-other", response.context["selected_brands"])
        self.assertTrue(response.context["stock_only"])
        skin = next(
            group for group in response.context["filter_groups"]
            if group["attribute"].code == "skin_type"
        )
        self.assertIn("sukha-sort", skin["selected_slugs"])
        self.assertNotIn("zhyrna-sort", skin["selected_slugs"])

        html = response.content.decode()
        self.assertIn('name="brand" value="sort-kept" checked', html)
        self.assertNotIn('name="brand" value="sort-other" checked', html)
        self.assertIn('name="skin_type" value="sukha-sort" checked', html)
        self.assertNotIn('name="skin_type" value="zhyrna-sort" checked', html)
        self.assertIn('name="stock" value="1" checked', html)
        self.assertNotContains(response, "ДельтаКрем")
        self.assertNotContains(response, "ЕпсилонКрем")
        self.assertNotContains(response, "ЗетаКрем")

        self.assertRegex(
            html,
            r'id="catalog-sort-current"[^>]*>\s*Ціна: спадання\s*</span>',
        )
        self.assertRegex(html, r'data-value="price-desc"\s+aria-selected="true"')
        self.assertEqual(html.count('aria-selected="true"'), 1)
        self.assertIn('<option value="price-desc" selected>Ціна: спадання</option>', html)
        self.assertEqual(len(re.findall(r"<option\b[^>]*\sselected\b", html)), 1)
        self.assertContains(response, "js/catalog.js?v=sort-mobile")
