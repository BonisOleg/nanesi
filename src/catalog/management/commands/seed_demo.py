"""Наповнення демо-даними: StaticPage + каталог (тестові SKU клієнта) + SEO-лендінг.

Запуск: python3 manage.py seed_demo
Ідемпотентно: update_or_create за slug/sku/path.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from src.catalog.models import Brand, Category, Product, ProductImage, ProductVariant, Supplier
from ._seed_demo_data import (
    BRANDS,
    CATEGORIES,
    PRODUCTS,
    SEO_LANDING,
    STATIC_PAGES,
    SUPPLIER_NAME,
    TRUST_BADGES,
)
from src.content.models import StaticPage, TrustBadge
from src.seo.models import SeoLandingPage

STATIC_PRODUCT_DIR = Path(settings.BASE_DIR) / "static" / "img" / "products"


class Command(BaseCommand):
    help = "Сидить StaticPage, тестовий каталог (5 SKU), TrustBadge і SEO-лендінг"

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_pages()
        self._seed_trust()
        brands, categories, supplier = self._seed_catalog_refs()
        products = self._seed_products(brands, categories, supplier)
        self._seed_seo(products)
        self.stdout.write(self.style.SUCCESS(
            f"OK: pages={StaticPage.objects.count()}, products={Product.objects.count()}, "
            f"variants={ProductVariant.objects.count()}, seo={SeoLandingPage.objects.count()}"
        ))

    def _seed_pages(self) -> None:
        for item in STATIC_PAGES:
            page, created = StaticPage.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "title": item["title"],
                    "body": item["body"],
                    "is_published": True,
                },
            )
            verb = "created" if created else "updated"
            self.stdout.write(f"  page {verb}: /{page.slug}/")

    def _seed_trust(self) -> None:
        for item in TRUST_BADGES:
            TrustBadge.objects.update_or_create(
                title=item["title"],
                defaults={
                    "icon_label": item["icon_label"],
                    "text": item["text"],
                    "is_active": True,
                    "sort_order": item["sort_order"],
                },
            )

    def _seed_catalog_refs(self) -> tuple[dict, dict, Supplier]:
        supplier, _ = Supplier.objects.get_or_create(
            name=SUPPLIER_NAME, defaults={"is_active": True},
        )
        brands: dict[str, Brand] = {}
        for item in BRANDS:
            brand, _ = Brand.objects.update_or_create(
                slug=item["slug"],
                defaults={"name": item["name"], "is_active": True},
            )
            brands[item["slug"]] = brand

        categories: dict[str, Category] = {}
        # спочатку корені, потім діти (дані впорядковані)
        for item in CATEGORIES:
            parent = categories.get(item["parent"]) if item["parent"] else None
            cat, _ = Category.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "parent": parent,
                    "is_active": True,
                    "sort_order": item["sort"],
                },
            )
            categories[item["slug"]] = cat
        return brands, categories, supplier

    def _seed_products(
        self,
        brands: dict[str, Brand],
        categories: dict[str, Category],
        supplier: Supplier,
    ) -> list[Product]:
        result: list[Product] = []
        for item in PRODUCTS:
            product, created = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "name": item["name"],
                    "brand": brands[item["brand"]],
                    "category": categories[item["category"]],
                    "supplier": supplier,
                    "short_description": item["short_description"],
                    "description": item["description"],
                    "usage_instructions": item["usage_instructions"],
                    "actives": item["actives"],
                    "inci": item["inci"],
                    "is_active": True,
                    "is_hit": item["is_hit"],
                    "is_new": item["is_new"],
                },
            )
            for idx, v in enumerate(item["variants"]):
                ProductVariant.objects.update_or_create(
                    sku=v["sku"],
                    defaults={
                        "product": product,
                        "barcode": v.get("barcode", ""),
                        "shade": v.get("shade", ""),
                        "volume": v.get("volume", ""),
                        "cost_price": v["cost_price"],
                        "retail_price": v["retail_price"],
                        "sale_price": v.get("sale_price"),
                        "stock_quantity": v["stock_quantity"],
                        "is_active": True,
                        "sort_order": idx,
                    },
                )
            self._attach_image(product, item["image"])
            verb = "created" if created else "updated"
            self.stdout.write(f"  product {verb}: /tovar/{product.slug}/")
            result.append(product)
        return result

    def _attach_image(self, product: Product, filename: str) -> None:
        src = STATIC_PRODUCT_DIR / filename
        if not src.is_file():
            self.stdout.write(self.style.WARNING(f"  skip image (missing): {filename}"))
            return
        if product.images.filter(is_main=True).exists():
            return
        with src.open("rb") as fh:
            img = ProductImage(product=product, alt_text=product.name, is_main=True, sort_order=0)
            img.image.save(filename, File(fh), save=True)

    def _seed_seo(self, products: list[Product]) -> None:
        landing, created = SeoLandingPage.objects.update_or_create(
            path=SEO_LANDING["path"],
            defaults={
                "title": SEO_LANDING["title"],
                "meta_title": SEO_LANDING["meta_title"],
                "meta_description": SEO_LANDING["meta_description"],
                "body": SEO_LANDING["body"],
                "is_indexed": SEO_LANDING["is_indexed"],
                "is_active": SEO_LANDING["is_active"],
            },
        )
        landing.products.set(products[:3])
        verb = "created" if created else "updated"
        self.stdout.write(f"  seo {verb}: /{landing.path}/ → {landing.get_absolute_url()}")
