"""Наповнення демо-даними: StaticPage + каталог (тестові SKU клієнта) + SEO-лендінг.

Запуск: python3 manage.py seed_demo
Ідемпотентно: update_or_create за slug/sku/path.
"""
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from src.catalog.models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Collection,
    Product,
    ProductImage,
    ProductVariant,
    Supplier,
)
from ._seed_demo_attrs import ATTRIBUTE_GROUPS, ATTRIBUTE_VALUES, PRODUCT_ATTRIBUTES, UMBRELLA_VALUE_SLUGS
from ._seed_demo_data import (
    BRANDS,
    CATEGORIES,
    PRODUCTS as CARE_PRODUCTS,
    SEO_LANDING,
    STATIC_PAGES,
    SUPPLIER_NAME,
    TRUST_BADGES,
)
from ._seed_demo_makeup import MAKEUP_PRODUCTS
from ._seed_demo_kbeauty_brand import KBEAUTY_BRAND_PRODUCTS
from src.content.models import SiteSettings, StaticPage, TrustBadge
from src.seo.models import SeoLandingPage

STATIC_PRODUCT_DIR = Path(settings.BASE_DIR) / "static" / "img" / "products"
STATIC_CATEGORY_DIR = Path(settings.BASE_DIR) / "static" / "img" / "categories"
COLLECTION_IMAGES = {
    "hity": "centella-serum.png",
    "novynky": "sunscreen.png",
    "aktsii": "pdrn-cream.png",
    "makiyazh-z-spf": "bb-cushion.png",
}

PRODUCTS = [*CARE_PRODUCTS, *MAKEUP_PRODUCTS, *KBEAUTY_BRAND_PRODUCTS]
CATEGORY_IMAGES = {
    "doglyad-za-oblychchyam": "doglyad-za-oblychchyam.png",
    "makiyazh": "makiyazh.png",
    "doglyad-za-tilom": "doglyad-za-tilom.png",
    "doglyad-za-volossyam": "doglyad-za-volossyam.png",
    "soncezahyst-spf": "soncezahyst-spf.png",
    "nabory-ta-miniatyury": "nabory-ta-miniatyury.png",
    "k-beauty": "k-beauty.png",
}


class Command(BaseCommand):
    help = "Сидить StaticPage, тестовий каталог (5 SKU), TrustBadge і SEO-лендінг"

    @transaction.atomic
    def handle(self, *args, **options):
        self._seed_pages()
        self._seed_trust()
        self._seed_site_settings()
        brands, categories, supplier = self._seed_catalog_refs()
        products = self._seed_products(brands, categories, supplier)
        attr_values = self._seed_attributes()
        self._seed_product_attributes(products, attr_values)
        self._seed_seo(products)
        self._seed_collections()

        self.stdout.write(self.style.SUCCESS(
            f"OK: pages={StaticPage.objects.count()}, products={Product.objects.count()}, "
            f"variants={ProductVariant.objects.count()}, attrs={Attribute.objects.count()}, "
            f"seo={SeoLandingPage.objects.count()}"
        ))

    def _seed_site_settings(self) -> None:
        site = SiteSettings.load()
        if not site.instagram_url:
            site.instagram_url = "https://instagram.com/nanesi.ua"
            site.save(update_fields=["instagram_url"])

    def _seed_collections(self) -> None:
        # Підбірки для головної /dobirka/ — 4 промо як у макеті
        specs = (
            (Collection.Kind.HIT, "Хіти продажів", "hity", 1),
            (Collection.Kind.NEW, "Новинки", "novynky", 2),
            (Collection.Kind.SALE, "Акції", "aktsii", 3),
            (Collection.Kind.CUSTOM, "Макіяж з SPF", "makiyazh-z-spf", 4),
        )
        for kind, name, slug, order in specs:
            col, _ = Collection.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "kind": kind, "is_active": True, "sort_order": order},
            )
            fname = COLLECTION_IMAGES.get(slug)
            if not fname or col.image:
                continue
            path = STATIC_PRODUCT_DIR / fname
            if path.exists():
                with path.open("rb") as fh:
                    col.image.save(fname, File(fh), save=True)

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
        keep_ids: list[int] = []
        for item in TRUST_BADGES:
            badge, _ = TrustBadge.objects.update_or_create(
                sort_order=item["sort_order"],
                defaults={
                    "icon_label": item["icon_label"],
                    "title": item["title"],
                    "text": item["text"],
                    "is_active": True,
                },
            )
            keep_ids.append(badge.pk)
        TrustBadge.objects.exclude(pk__in=keep_ids).update(is_active=False)

    def _seed_catalog_refs(self) -> tuple[dict, dict, Supplier]:
        supplier, _ = Supplier.objects.get_or_create(
            name=SUPPLIER_NAME, defaults={"is_active": True},
        )
        brands: dict[str, Brand] = {}
        for item in BRANDS:
            brand, created = Brand.objects.get_or_create(
                slug=item["slug"],
                defaults={"name": item["name"], "is_active": True},
            )
            if not created and not brand.is_active:
                brand.is_active = True
                brand.save(update_fields=["is_active"])
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
                    "show_in_header": bool(item.get("show_in_header", False)),
                    "sort_order": item["sort"],
                },
            )
            categories[item["slug"]] = cat
            self._attach_category_image(cat)
        return brands, categories, supplier

    def _attach_category_image(self, category: Category) -> None:
        fname = CATEGORY_IMAGES.get(category.slug)
        if not fname or category.image:
            return
        path = STATIC_CATEGORY_DIR / fname
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  skip category image (missing): {fname}"))
            return
        with path.open("rb") as fh:
            category.image.save(fname, File(fh), save=True)

    def _seed_attributes(self) -> dict[str, dict[str, AttributeValue]]:
        """Повертає {attribute.code: {value.slug: AttributeValue}}."""
        by_code: dict[str, dict[str, AttributeValue]] = {}
        for group in ATTRIBUTE_GROUPS:
            attr, _ = Attribute.objects.update_or_create(
                code=group["code"],
                defaults={
                    "name": group["name"],
                    "is_filterable": True,
                    "show_on_pdp": group.get("show_on_pdp", True),
                    "sort_order": group["sort"],
                },
            )
            by_code[attr.code] = {}
            for order, (slug, label) in enumerate(ATTRIBUTE_VALUES.get(attr.code, []), start=1):
                value, _ = AttributeValue.objects.update_or_create(
                    attribute=attr,
                    value=label,
                    defaults={
                        "slug": slug,
                        "sort_order": order * 10,
                        "is_umbrella": slug in UMBRELLA_VALUE_SLUGS,
                    },
                )
                if value.slug != slug:
                    value.slug = slug
                    value.save(update_fields=["slug"])
                by_code[attr.code][slug] = value
            self.stdout.write(f"  attribute: {attr.code} ({len(by_code[attr.code])} values)")
        return by_code

    def _seed_product_attributes(
        self,
        products: list[Product],
        attr_values: dict[str, dict[str, AttributeValue]],
    ) -> None:
        by_slug = {p.slug: p for p in products}
        for product_slug, groups in PRODUCT_ATTRIBUTES.items():
            product = by_slug.get(product_slug)
            if product is None:
                self.stdout.write(self.style.WARNING(f"  skip attrs (no product): {product_slug}"))
                continue
            selected: list[AttributeValue] = []
            for code, slugs in groups.items():
                bucket = attr_values.get(code, {})
                for slug in slugs:
                    value = bucket.get(slug)
                    if value is None:
                        self.stdout.write(
                            self.style.WARNING(f"  skip value {code}/{slug} for {product_slug}")
                        )
                        continue
                    selected.append(value)
            product.attribute_values.set(selected)
            self.stdout.write(f"  product attrs: {product_slug} ({len(selected)})")

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
                        "shade_hex": v.get("shade_hex", ""),
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
            extra_slugs = item.get("additional")
            if extra_slugs is None:
                extra_slugs = ["k-beauty"] if "k-beauty" in categories else []
            extra_cats = [categories[slug] for slug in extra_slugs if slug in categories]
            product.additional_categories.set(extra_cats)
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
