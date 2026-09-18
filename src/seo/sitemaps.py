"""sitemap.xml: i18n alternates лише для мов, увімкнених у SiteSettings."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from src.catalog.models import Brand, Category, Collection, Product
from src.content.models import BlogPost, StaticPage
from src.seo.models import SeoLandingPage
from src.seo.utils import enabled_language_codes


class EnabledLangSitemap(Sitemap):
    i18n = True
    x_default = True

    def _languages(self):
        return enabled_language_codes()


class ProductSitemap(EnabledLangSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(EnabledLangSitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class BrandSitemap(EnabledLangSitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return Brand.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CollectionSitemap(EnabledLangSitemap):
    changefreq = "weekly"
    priority = 0.45

    def items(self):
        return Collection.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(EnabledLangSitemap):
    changefreq = "monthly"
    priority = 0.4

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticPageSitemap(EnabledLangSitemap):
    changefreq = "yearly"
    priority = 0.3

    def items(self):
        return StaticPage.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class SeoLandingPageSitemap(EnabledLangSitemap):
    """Лише проіндексовані (is_indexed=True) — noindex-лендінги в sitemap не потрібні."""

    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return SeoLandingPage.objects.filter(is_active=True, is_indexed=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(EnabledLangSitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return ["catalog:home", "catalog:catalog", "catalog:brand_list", "content:blog_list"]

    def location(self, item):
        return reverse(item)


sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "brands": BrandSitemap,
    "collections": CollectionSitemap,
    "blog": BlogPostSitemap,
    "pages": StaticPageSitemap,
    "seo-landings": SeoLandingPageSitemap,
}
