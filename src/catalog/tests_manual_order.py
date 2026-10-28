"""Ручний порядок товарів у категорії та позиція в підбірці."""
import re
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from src.catalog.models import (
    Brand,
    Category,
    CategoryProductPosition,
    Collection,
    CollectionProduct,
    Product,
    ProductVariant,
    Review,
)
from src.catalog.selectors import products_for_collection


def _product(brand, category, name, slug, *, created_at=None, is_hit=False):
    product = Product.objects.create(
        name=name,
        slug=slug,
        brand=brand,
        category=category,
        is_active=True,
        is_hit=is_hit,
    )
    ProductVariant.objects.create(
        product=product,
        sku=slug,
        retail_price=Decimal("100.00"),
        stock_quantity=5,
        is_active=True,
    )
    if created_at is not None:
        Product.objects.filter(pk=product.pk).update(created_at=created_at)
        product.created_at = created_at
    return product


class CategoryProductPositionModelTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Бренд", slug="brand-pos")
        self.category = Category.objects.create(name="Крем", slug="krem-pos")
        self.product = _product(self.brand, self.category, "Крем А", "krem-a")

    def test_unique_category_product(self):
        CategoryProductPosition.objects.create(
            category=self.category, product=self.product, position=1,
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CategoryProductPosition.objects.create(
                    category=self.category, product=self.product, position=2,
                )

    def test_missing_row_means_no_position(self):
        self.assertFalse(
            CategoryProductPosition.objects.filter(product=self.product).exists()
        )


class CollectionProductOrderTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Бренд", slug="brand-col")
        self.category = Category.objects.create(name="Сироватка", slug="syr-col")
        now = timezone.now()
        self.oldest = _product(
            self.brand, self.category, "Старий", "staryi",
            created_at=now - timedelta(days=3),
        )
        self.middle = _product(
            self.brand, self.category, "Середній", "serednii",
            created_at=now - timedelta(days=2),
        )
        self.newest = _product(
            self.brand, self.category, "Новий", "novyi",
            created_at=now - timedelta(days=1),
        )
        self.collection = Collection.objects.create(
            name="Добірка", slug="dobirka-order", kind=Collection.Kind.CUSTOM,
        )

    def test_add_sets_position_zero_on_existing_m2m_table(self):
        self.assertEqual(CollectionProduct._meta.db_table, "catalog_collection_products")
        self.collection.products.add(self.oldest, self.newest)
        rows = CollectionProduct.objects.filter(collection=self.collection)
        self.assertEqual(rows.count(), 2)
        self.assertTrue(all(row.position == 0 for row in rows))

    def test_collection_lists_products_by_position(self):
        self.collection.products.add(self.oldest, self.middle, self.newest)
        CollectionProduct.objects.filter(
            collection=self.collection, product=self.newest,
        ).update(position=0)
        CollectionProduct.objects.filter(
            collection=self.collection, product=self.oldest,
        ).update(position=1)
        CollectionProduct.objects.filter(
            collection=self.collection, product=self.middle,
        ).update(position=2)

        ordered = list(products_for_collection(self.collection))
        self.assertEqual(
            [item.pk for item in ordered],
            [self.newest.pk, self.oldest.pk, self.middle.pk],
        )

        response = self.client.get(self.collection.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        positions = [html.find(name) for name in ("Новий", "Старий", "Середній")]
        self.assertTrue(all(pos >= 0 for pos in positions))
        self.assertEqual(positions, sorted(positions))

    def test_empty_m2m_falls_back_to_kind(self):
        hits = Collection.objects.create(
            name="Хіти", slug="hity-order", kind=Collection.Kind.HIT,
        )
        self.newest.is_hit = True
        self.newest.save(update_fields=["is_hit"])
        ordered = list(products_for_collection(hits))
        self.assertEqual([item.pk for item in ordered], [self.newest.pk])


def _selected_sort(html: str) -> str:
    match = re.search(r'data-value="([^"]+)"\s+aria-selected="true"', html)
    if match is None:
        raise AssertionError("немає вибраного сортування")
    return match.group(1)


def _assert_name_order(test, html: str, names: list[str]) -> None:
    positions = [html.find(name) for name in names]
    test.assertTrue(all(pos >= 0 for pos in positions), positions)
    test.assertEqual(positions, sorted(positions))


class ManualCatalogSortTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Nane", slug="nane")
        self.category = Category.objects.create(name="Тонери", slug="tonery")
        now = timezone.now()
        self.pos_low = _product(
            self.brand, self.category, "АльфаПоз", "alfa-poz",
            created_at=now - timedelta(days=1),
        )
        self.pos_high = _product(
            self.brand, self.category, "БетаПоз", "beta-poz",
            created_at=now - timedelta(days=2),
        )
        self.rated = _product(
            self.brand, self.category, "РейтингТоп", "reitynh-top",
            created_at=now - timedelta(days=10),
        )
        self.tie_low = _product(
            self.brand, self.category, "НічияОдин", "nichyia-1",
            created_at=now - timedelta(days=3),
        )
        self.tie_high = _product(
            self.brand, self.category, "НічияДва", "nichyia-2",
            created_at=now - timedelta(days=4),
        )
        same = now - timedelta(days=3)
        Product.objects.filter(pk__in=[self.tie_low.pk, self.tie_high.pk]).update(created_at=same)
        CategoryProductPosition.objects.create(
            category=self.category, product=self.pos_low, position=0,
        )
        CategoryProductPosition.objects.create(
            category=self.category, product=self.pos_high, position=5,
        )
        Review.objects.create(
            product=self.rated, rating=5, text="Добре", is_approved=True,
        )
        self.manual_names = ["АльфаПоз", "БетаПоз", "РейтингТоп", "НічияОдин", "НічияДва"]
        self.popular_names = ["РейтингТоп", "АльфаПоз", "БетаПоз", "НічияОдин", "НічияДва"]

    def test_category_default_is_manual_with_nulls_last(self):
        response = self.client.get(self.category.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertEqual(_selected_sort(html), "manual")
        self.assertContains(response, "Ручний порядок")
        _assert_name_order(self, html, self.manual_names)

    def test_query_and_brand_filter_keep_popular_default(self):
        by_query = self.client.get(self.category.get_absolute_url(), {"q": "Nane"})
        self.assertEqual(_selected_sort(by_query.content.decode()), "popular")
        _assert_name_order(self, by_query.content.decode(), self.popular_names)

        by_brand = self.client.get(self.category.get_absolute_url(), {"brand": "nane"})
        self.assertEqual(_selected_sort(by_brand.content.decode()), "popular")
        _assert_name_order(self, by_brand.content.decode(), self.popular_names)

    def test_explicit_sort_manual_wins_with_filter(self):
        response = self.client.get(
            self.category.get_absolute_url(),
            {"brand": "nane", "sort": "manual"},
        )
        html = response.content.decode()
        self.assertEqual(_selected_sort(html), "manual")
        _assert_name_order(self, html, self.manual_names)

    def test_explicit_popular_and_name_on_category(self):
        popular = self.client.get(self.category.get_absolute_url(), {"sort": "popular"})
        self.assertEqual(_selected_sort(popular.content.decode()), "popular")
        _assert_name_order(self, popular.content.decode(), self.popular_names)

        by_name = self.client.get(self.category.get_absolute_url(), {"sort": "name"})
        _assert_name_order(
            self,
            by_name.content.decode(),
            ["АльфаПоз", "БетаПоз", "НічияДва", "НічияОдин", "РейтингТоп"],
        )

    def test_manual_without_category_behaves_as_popular(self):
        response = self.client.get(reverse("catalog:catalog"), {"sort": "manual"})
        html = response.content.decode()
        self.assertEqual(_selected_sort(html), "manual")
        _assert_name_order(self, html, self.popular_names)


class ParentCategoryManualSortTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Nane", slug="nane-parent")
        self.parent = Category.objects.create(name="Догляд", slug="doglyad")
        self.child = Category.objects.create(name="Креми", slug="kremy", parent=self.parent)
        self.from_child = _product(self.brand, self.child, "ЗПіддерева", "z-piddereva")
        self.on_parent = _product(self.brand, self.parent, "УБатька", "u-batka")
        self.child_only = _product(self.brand, self.child, "БезПозиціїБатька", "bez-pozytsii")
        CategoryProductPosition.objects.create(
            category=self.parent, product=self.from_child, position=0,
        )
        CategoryProductPosition.objects.create(
            category=self.parent, product=self.on_parent, position=1,
        )
        CategoryProductPosition.objects.create(
            category=self.child, product=self.child_only, position=0,
        )

    def test_parent_uses_own_positions_and_subtree_products(self):
        parent_page = self.client.get(self.parent.get_absolute_url())
        _assert_name_order(
            self,
            parent_page.content.decode(),
            ["ЗПіддерева", "УБатька", "БезПозиціїБатька"],
        )
        child_page = self.client.get(self.child.get_absolute_url())
        _assert_name_order(
            self,
            child_page.content.decode(),
            ["БезПозиціїБатька", "ЗПіддерева"],
        )
