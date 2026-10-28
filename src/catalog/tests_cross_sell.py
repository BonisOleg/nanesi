"""Ручний cross-sell «З цим купують»: порядок, фолбек, ліміт, адмінка."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from src.catalog.models import Brand, Category, Product, ProductCrossSell, ProductVariant
from src.catalog.selectors import bought_together, visible_products


class CrossSellTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Round Lab", slug="round-lab")
        self.other_brand = Brand.objects.create(name="COSRX", slug="cosrx")
        self.category = Category.objects.create(name="Сироватки", slug="syrovatky")
        self.other_category = Category.objects.create(name="Креми", slug="kremy")
        self.anchor = self._product("Anchor", "anchor")
        self.hit = self._product("Hit", "hit", is_hit=True)
        self.fresh = self._product("Fresh", "fresh")
        self.mid = self._product("Mid", "mid")
        self.old_brand = self._product("Old brand", "old-brand", category=self.other_category)
        self.oldest = self._product("Oldest", "oldest")
        self.outsider = self._product(
            "Outsider", "outsider", brand=self.other_brand, category=self.other_category,
        )
        self.inactive = self._product("Inactive", "inactive", is_active=False)
        self._stamp(self.hit, 3)
        self._stamp(self.fresh, 1)
        self._stamp(self.mid, 5)
        self._stamp(self.old_brand, 9)
        self._stamp(self.oldest, 30)

    def _product(self, name, slug, *, brand=None, category=None, is_active=True, is_hit=False, stock=3):
        product = Product.objects.create(
            name=name,
            slug=slug,
            brand=brand or self.brand,
            category=category or self.category,
            is_active=is_active,
            is_hit=is_hit,
        )
        ProductVariant.objects.create(
            product=product,
            sku=f"SKU-{slug}",
            retail_price="100.00",
            stock_quantity=stock,
            is_active=True,
        )
        return product

    def _stamp(self, product, days_ago):
        Product.objects.filter(pk=product.pk).update(
            created_at=timezone.now() - timedelta(days=days_ago),
        )

    def _auto_pks(self, product=None, limit=4):
        product = product or self.anchor
        return list(
            visible_products()
            .filter(Q(category=product.category) | Q(brand=product.brand))
            .exclude(pk=product.pk)
            .order_by("-is_hit", "-rating_avg", "-created_at")
            .values_list("pk", flat=True)[:limit]
        )

    def test_manual_order_respected_in_pdp_context(self):
        low_id = self._product(
            "Low", "low-id", brand=self.other_brand, category=self.other_category,
        )
        high_id = self._product(
            "High", "high-id", brand=self.other_brand, category=self.other_category, stock=0,
        )
        first = self._product(
            "First", "first-pos", brand=self.other_brand, category=self.other_category,
        )
        ProductCrossSell.objects.create(from_product=self.anchor, to_product=high_id, position=1)
        ProductCrossSell.objects.create(from_product=self.anchor, to_product=low_id, position=1)
        ProductCrossSell.objects.create(from_product=self.anchor, to_product=first, position=0)
        expected = [first, high_id, low_id]

        with self.assertNumQueries(3):
            self.assertEqual(bought_together(self.anchor), expected)

        response = self.client.get(reverse("catalog:product_detail", kwargs={"slug": self.anchor.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["bought_together_products"]), expected)
        self.assertNotIn(self.hit, response.context["bought_together_products"])

    def test_empty_manual_matches_auto(self):
        self.assertFalse(ProductCrossSell.objects.filter(from_product=self.anchor).exists())
        self.assertEqual([item.pk for item in bought_together(self.anchor)], self._auto_pks())
        self.assertEqual(self._auto_pks(), [self.hit.pk, self.fresh.pk, self.mid.pk, self.old_brand.pk])

    def test_all_inactive_manual_falls_back_to_auto(self):
        hidden = self._product("Hidden mate", "hidden-mate", is_active=False)
        ProductCrossSell.objects.create(from_product=self.anchor, to_product=hidden, position=0)
        ProductCrossSell.objects.create(from_product=self.anchor, to_product=self.inactive, position=1)
        result = bought_together(self.anchor)
        self.assertEqual([item.pk for item in result], self._auto_pks())
        self.assertNotIn(hidden, result)
        self.assertNotIn(self.inactive, result)

    def test_unpublished_excluded(self):
        visible = self._product(
            "Visible mate", "visible-mate", brand=self.other_brand, category=self.other_category,
        )
        hidden = self._product(
            "Hidden mate", "hidden-only", brand=self.other_brand, category=self.other_category,
            is_active=False,
        )
        ProductCrossSell.objects.create(from_product=self.anchor, to_product=hidden, position=0)
        ProductCrossSell.objects.create(from_product=self.anchor, to_product=visible, position=1)
        self.assertEqual(bought_together(self.anchor), [visible])

    def test_max_eight(self):
        anchor = self._product(
            "Cap", "cap-anchor", brand=self.other_brand, category=self.other_category,
        )
        targets = [
            self._product(
                f"Cap {index}", f"cap-{index}", brand=self.other_brand, category=self.other_category,
            )
            for index in range(10)
        ]
        for index in range(9, -1, -1):
            ProductCrossSell.objects.create(
                from_product=anchor, to_product=targets[index], position=index,
            )
        self.assertEqual(bought_together(anchor, limit=4), targets[:4])
        capped = bought_together(anchor, limit=100)
        self.assertEqual(capped, targets[:8])
        self.assertEqual(len(capped), 8)

    def test_asymmetry(self):
        brand_a = Brand.objects.create(name="Brand A", slug="brand-a")
        brand_b = Brand.objects.create(name="Brand B", slug="brand-b")
        category_a = Category.objects.create(name="Cat A", slug="cat-a")
        category_b = Category.objects.create(name="Cat B", slug="cat-b")
        product_a = self._product("A", "prod-a", brand=brand_a, category=category_a)
        product_b = self._product("B", "prod-b", brand=brand_b, category=category_b)
        ProductCrossSell.objects.create(from_product=product_a, to_product=product_b, position=0)

        self.assertEqual(list(product_a.cross_sell.all()), [product_b])
        self.assertEqual(list(product_b.cross_sell.all()), [])
        self.assertEqual(bought_together(product_a), [product_b])
        self.assertEqual(bought_together(product_b), [])
        self.assertFalse(
            ProductCrossSell.objects.filter(from_product=product_b, to_product=product_a).exists()
        )

    def test_self_link_raises_integrity_error(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ProductCrossSell.objects.create(
                    from_product=self.anchor,
                    to_product=self.anchor,
                    position=0,
                )

    def test_admin_product_change_contains_inline(self):
        user = get_user_model().objects.create_superuser("admin", "a@b.c", "pass")
        self.client.force_login(user)
        response = self.client.get(reverse("admin:catalog_product_change", args=[self.anchor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "З цим купують")
        self.assertContains(response, "cross_sell_links-group")
