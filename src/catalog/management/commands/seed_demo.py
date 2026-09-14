"""Наповнення демо-даними: StaticPage + каталог (тестові SKU клієнта) + SEO-лендінг.

Запуск: python3 manage.py seed_demo
Ідемпотентно: update_or_create за slug/sku/path.
"""
from decimal import Decimal
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
    HERO_BANNERS_STOCK,
    PRODUCTS as CARE_PRODUCTS,
    SEO_LANDING,
    STATIC_PAGES,
    SUPPLIER_NAME,
    TRUST_BADGES,
    BLOG_POSTS,
)
from ._seed_demo_i18n import (
    ATTR_GROUPS_I18N,
    ATTR_VALUES_I18N,
    BLOG_POSTS_I18N,
    BRANDS_I18N,
    CATEGORIES_I18N,
    COLLECTIONS_I18N,
    PAGES_I18N,
    PRODUCTS_I18N,
    SITE_SETTINGS_I18N,
    TRUST_I18N,
    merge_i18n,
)
from ._seed_demo_i18n_2 import PRODUCTS_LONG_I18N
from ._seed_demo_makeup import MAKEUP_PRODUCTS
from ._seed_demo_kbeauty_brand import KBEAUTY_BRAND_PRODUCTS
from src.content.models import BlogPost, HeroBanner, SiteSettings, StaticPage, TrustBadge
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
        self._seed_hero_banners()
        brands, categories, supplier = self._seed_catalog_refs()
        products = self._seed_products(brands, categories, supplier)
        attr_values = self._seed_attributes()
        self._seed_product_attributes(products, attr_values)
        self._seed_seo(products)
        self._seed_collections()
        self._seed_blog()

        self.stdout.write(self.style.SUCCESS(
            f"OK: pages={StaticPage.objects.count()}, products={Product.objects.count()}, "
            f"variants={ProductVariant.objects.count()}, attrs={Attribute.objects.count()}, "
            f"seo={SeoLandingPage.objects.count()}, blog={BlogPost.objects.count()}"
        ))

    def _seed_site_settings(self) -> None:
        site = SiteSettings.load()
        updates: list[str] = []
        if not site.instagram_url:
            site.instagram_url = "https://instagram.com/nanesi.ua"
            updates.append("instagram_url")
        if not site.free_shipping_threshold:
            site.free_shipping_threshold = Decimal("1500.00")
            updates.append("free_shipping_threshold")
        if not site.card_payment_enabled:
            site.card_payment_enabled = True
            updates.append("card_payment_enabled")
        for field, value in SITE_SETTINGS_I18N.items():
            if getattr(site, field, None) != value:
                setattr(site, field, value)
                updates.append(field)
        if updates:
            site.save(update_fields=updates)

    def _seed_blog(self) -> None:
        from django.utils.dateparse import parse_datetime

        for item in BLOG_POSTS:
            published_at = parse_datetime(item["published_at"])
            defaults = merge_i18n(
                {
                    "title": item["title"],
                    "body": item["body"],
                    "is_published": True,
                    "published_at": published_at,
                },
                BLOG_POSTS_I18N.get(item["slug"]),
            )
            post, created = BlogPost.objects.update_or_create(
                slug=item["slug"],
                defaults=defaults,
            )
            verb = "created" if created else "updated"
            self.stdout.write(f"  blog {verb}: /blog/{post.slug}/")

    def _seed_collections(self) -> None:
        # Підбірки для головної /dobirka/ — 4 промо як у макеті
        specs = (
            (Collection.Kind.HIT, "Хіти продажів", "hity", 1),
            (Collection.Kind.NEW, "Новинки", "novynky", 2),
            (Collection.Kind.SALE, "Акції", "aktsii", 3),
            (Collection.Kind.CUSTOM, "Макіяж з SPF", "makiyazh-z-spf", 4),
        )
        for kind, name, slug, order in specs:
            defaults = merge_i18n(
                {"name": name, "kind": kind, "is_active": True, "sort_order": order},
                COLLECTIONS_I18N.get(slug),
            )
            col, _ = Collection.objects.update_or_create(slug=slug, defaults=defaults)
            fname = COLLECTION_IMAGES.get(slug)
            if not fname or col.image:
                continue
            path = STATIC_PRODUCT_DIR / fname
            if path.exists():
                with path.open("rb") as fh:
                    col.image.save(fname, File(fh), save=True)

    def _seed_pages(self) -> None:
        for item in STATIC_PAGES:
            defaults = merge_i18n(
                {
                    "title": item["title"],
                    "body": item["body"],
                    "is_published": True,
                },
                PAGES_I18N.get(item["slug"]),
            )
            page, created = StaticPage.objects.update_or_create(
                slug=item["slug"],
                defaults=defaults,
            )
            verb = "created" if created else "updated"
            self.stdout.write(f"  page {verb}: /{page.slug}/")

    def _seed_trust(self) -> None:
        keep_ids: list[int] = []
        for item in TRUST_BADGES:
            defaults = merge_i18n(
                {
                    "icon_label": item["icon_label"],
                    "title": item["title"],
                    "text": item["text"],
                    "is_active": True,
                },
                TRUST_I18N.get(item["sort_order"]),
            )
            badge, _ = TrustBadge.objects.update_or_create(
                sort_order=item["sort_order"],
                defaults=defaults,
            )
            keep_ids.append(badge.pk)
        TrustBadge.objects.exclude(pk__in=keep_ids).update(is_active=False)

    def _seed_hero_banners(self) -> None:
        """3 слайди: #1 з SiteSettings.hero_*; #2–3 — сток. Поля мов — лише явні *_uk/ru/en."""
        site = SiteSettings.load()
        overlay_defaults = {
            "overlay_color": "#EFE9E1",
            "overlay_opacity": 72,
            "overlay_blur": 10,
        }
        eye_uk = " ".join(
            p for p in (
                SITE_SETTINGS_I18N.get("site_name_uk") or site.site_name_uk or site.site_name,
                SITE_SETTINGS_I18N.get("tagline_uk") or site.tagline_uk or site.tagline,
            ) if p
        ).strip() or "NANESI Beauty Store"
        eye_ru = " ".join(
            p for p in (
                SITE_SETTINGS_I18N.get("site_name_ru") or site.site_name_ru or site.site_name,
                SITE_SETTINGS_I18N.get("tagline_ru") or site.tagline_ru or site.tagline,
            ) if p
        ).strip() or eye_uk
        eye_en = " ".join(
            p for p in (
                SITE_SETTINGS_I18N.get("site_name_en") or site.site_name_en or site.site_name,
                SITE_SETTINGS_I18N.get("tagline_en") or site.tagline_en or site.tagline,
            ) if p
        ).strip() or eye_uk

        slide1_defaults = {
            "eyebrow_uk": eye_uk,
            "eyebrow_ru": eye_ru,
            "eyebrow_en": eye_en,
            "title_uk": SITE_SETTINGS_I18N.get("hero_title_uk") or site.hero_title_uk or site.hero_title,
            "title_ru": SITE_SETTINGS_I18N.get("hero_title_ru") or site.hero_title_ru or "",
            "title_en": SITE_SETTINGS_I18N.get("hero_title_en") or site.hero_title_en or "",
            "subtitle_uk": SITE_SETTINGS_I18N.get("hero_subtitle_uk") or site.hero_subtitle_uk or site.hero_subtitle,
            "subtitle_ru": SITE_SETTINGS_I18N.get("hero_subtitle_ru") or site.hero_subtitle_ru or "",
            "subtitle_en": SITE_SETTINGS_I18N.get("hero_subtitle_en") or site.hero_subtitle_en or "",
            "button_text_uk": "До каталогу",
            "button_text_ru": "В каталог",
            "button_text_en": "Shop now",
            "button_url": "/katalog/",
            "is_active": True,
            **overlay_defaults,
        }
        banner1, _ = HeroBanner.objects.update_or_create(
            sort_order=1,
            defaults=slide1_defaults,
        )
        if site.hero_image and not banner1.image:
            banner1.image = site.hero_image
            banner1.save(update_fields=["image"])

        keep_ids = [banner1.pk]
        banners_by_order = {1: banner1}
        for item in HERO_BANNERS_STOCK:
            defaults = {
                "eyebrow_uk": item["eyebrow"],
                "title_uk": item["title"],
                "subtitle_uk": item["subtitle"],
                "button_text_uk": item["button_text"],
                "button_url": item["button_url"],
                "is_active": True,
                **overlay_defaults,
                "overlay_blur": item.get("overlay_blur", 10),
                "overlay_opacity": item.get("overlay_opacity", 72),
            }
            for lang in ("ru", "en"):
                for field in ("eyebrow", "title", "subtitle", "button_text"):
                    key = f"{field}_{lang}"
                    if item.get(key):
                        defaults[key] = item[key]
            banner, _ = HeroBanner.objects.update_or_create(
                sort_order=item["sort_order"],
                defaults=defaults,
            )
            keep_ids.append(banner.pk)
            banners_by_order[item["sort_order"]] = banner

        bg_dir = Path(settings.BASE_DIR) / "static" / "img" / "hero"
        bg_files = {1: "bg-1.jpg", 2: "bg-2.jpg", 3: "bg-3.jpg"}
        for order, fname in bg_files.items():
            banner = banners_by_order.get(order)
            if banner is None or banner.background_image:
                continue
            path = bg_dir / fname
            if not path.exists():
                continue
            with path.open("rb") as fh:
                banner.background_image.save(fname, File(fh), save=True)

        deactivated = HeroBanner.objects.exclude(pk__in=keep_ids).update(is_active=False)
        self.stdout.write(f"  hero banners: {len(keep_ids)} active" + (
            f", deactivated extras: {deactivated}" if deactivated else ""
        ))

    def _seed_catalog_refs(self) -> tuple[dict, dict, Supplier]:
        supplier, _ = Supplier.objects.get_or_create(
            name=SUPPLIER_NAME, defaults={"is_active": True},
        )
        brands: dict[str, Brand] = {}
        for item in BRANDS:
            defaults = merge_i18n(
                {"name": item["name"], "is_active": True},
                BRANDS_I18N.get(item["slug"]),
            )
            brand, created = Brand.objects.update_or_create(
                slug=item["slug"],
                defaults=defaults,
            )
            brands[item["slug"]] = brand

        categories: dict[str, Category] = {}
        # спочатку корені, потім діти (дані впорядковані)
        for item in CATEGORIES:
            parent = categories.get(item["parent"]) if item["parent"] else None
            defaults = merge_i18n(
                {
                    "name": item["name"],
                    "parent": parent,
                    "is_active": True,
                    "show_in_header": bool(item.get("show_in_header", False)),
                    "sort_order": item["sort"],
                },
                CATEGORIES_I18N.get(item["slug"]),
            )
            cat, _ = Category.objects.update_or_create(
                slug=item["slug"],
                defaults=defaults,
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
            attr_defaults = merge_i18n(
                {
                    "name": group["name"],
                    "is_filterable": True,
                    "show_on_pdp": group.get("show_on_pdp", True),
                    "sort_order": group["sort"],
                },
                ATTR_GROUPS_I18N.get(group["code"]),
            )
            attr, _ = Attribute.objects.update_or_create(
                code=group["code"],
                defaults=attr_defaults,
            )
            by_code[attr.code] = {}
            for order, (slug, label) in enumerate(ATTRIBUTE_VALUES.get(attr.code, []), start=1):
                value_defaults = merge_i18n(
                    {
                        "slug": slug,
                        "sort_order": order * 10,
                        "is_umbrella": slug in UMBRELLA_VALUE_SLUGS,
                    },
                    ATTR_VALUES_I18N.get((attr.code, slug)),
                )
                value, _ = AttributeValue.objects.update_or_create(
                    attribute=attr,
                    value=label,
                    defaults=value_defaults,
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
            i18n = {
                **PRODUCTS_I18N.get(item["slug"], {}),
                **PRODUCTS_LONG_I18N.get(item["slug"], {}),
            }
            defaults = merge_i18n(
                {
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
                i18n,
            )
            product, created = Product.objects.update_or_create(
                slug=item["slug"],
                defaults=defaults,
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
        defaults = {
            "title_uk": SEO_LANDING["title"],
            "meta_title_uk": SEO_LANDING["meta_title"],
            "meta_description_uk": SEO_LANDING["meta_description"],
            "body_uk": SEO_LANDING["body"],
            "is_indexed": SEO_LANDING["is_indexed"],
            "is_active": SEO_LANDING["is_active"],
        }
        for lang in ("ru", "en"):
            for field in ("title", "meta_title", "meta_description", "body"):
                key = f"{field}_{lang}"
                if SEO_LANDING.get(key):
                    defaults[key] = SEO_LANDING[key]
        landing, created = SeoLandingPage.objects.update_or_create(
            path=SEO_LANDING["path"],
            defaults=defaults,
        )
        landing.products.set(products[:3])
        verb = "created" if created else "updated"
        self.stdout.write(f"  seo {verb}: /{landing.path}/ → {landing.get_absolute_url()}")
