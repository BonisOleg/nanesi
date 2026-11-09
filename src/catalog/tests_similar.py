"""Ручні «Схожі товари»: порядок, фолбек на категорію, адмінка."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from src.catalog.models import Brand, Category, Product, ProductSimilar, ProductVariant
from src.catalog.selectors import related_products


class SimilarProductsTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Round Lab", slug="round-lab")
        self.other_brand = Brand.objects.create(name="COSRX", slug="cosrx")
        self.category = Category.objects.create(name="Сироватки", slug="syrovatky")
        self.other_category = Category.objects.create(name="Креми", slug="kremy")
        self.anchor = self._product("Anchor", "anchor")
        self.cat_mate = self._product("Cat mate", "cat-mate")
        self.outsider = self._product(
            "Outsider", "outsider", brand=self.other_brand, category=self.other_category,
        )

    def _product(self, name, slug, *, brand=None, category=None, is_active=True):
        product = Product.objects.create(
            name=name,
            slug=slug,
            brand=brand or self.brand,
            category=category or self.category,
            is_active=is_active,
        )
        ProductVariant.objects.create(
            product=product,
            sku=f"SKU-{slug}",
            retail_price="100.00",
            stock_quantity=3,
            is_active=True,
        )
        return product

    def test_manual_order_preferred_over_auto(self):
        ProductSimilar.objects.create(from_product=self.anchor, to_product=self.outsider, position=0)
        ProductSimilar.objects.create(from_product=self.anchor, to_product=self.cat_mate, position=1)
        self.assertEqual(related_products(self.anchor), [self.outsider, self.cat_mate])

    def test_empty_manual_falls_back_to_category(self):
        result = related_products(self.anchor)
        self.assertIn(self.cat_mate, result)
        self.assertNotIn(self.outsider, result)

    def test_admin_product_change_contains_similar_inline(self):
        user = get_user_model().objects.create_superuser("admin", "a@b.c", "pass")
        self.client.force_login(user)
        response = self.client.get(reverse("admin:catalog_product_change", args=[self.anchor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Схожі товари")
        self.assertContains(response, "similar_links-group")
