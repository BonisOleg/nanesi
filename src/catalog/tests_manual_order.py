"""Ручний порядок товарів у категорії та позиція в підбірці."""
from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from src.catalog.models import (
    Brand,
    Category,
    CategoryProductPosition,
    Collection,
    CollectionProduct,
    Product,
    ProductVariant,
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
