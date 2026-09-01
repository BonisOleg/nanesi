"""sitemap.xml: усі публічні сторінки, i18n=True — по alternate-посиланню на кожну увімкнену мову."""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from src.catalog.models import Brand, Category, Product
from src.content.models import BlogPost, StaticPage
from src.seo.models import SeoLandingPage


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    i18n = True

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    i18n = True

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class BrandSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    i18n = True

    def items(self):
        return Brand.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4
    i18n = True

    def items(self):
        return BlogPost.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticPageSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.3
    i18n = True

    def items(self):
        return StaticPage.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at


class SeoLandingPageSitemap(Sitemap):
    """Лише проіндексовані (is_indexed=True) — noindex-лендінги в sitemap не потрібні."""

    changefreq = "monthly"
    priority = 0.5
    i18n = True

    def items(self):
        return SeoLandingPage.objects.filter(is_active=True, is_indexed=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0
    i18n = True

    def items(self):
        return ["catalog:home", "catalog:catalog", "catalog:brand_list", "content:blog_list"]

    def location(self, item):
        return reverse(item)


sitemaps = {
    "static": StaticViewSitemap,
    "products": ProductSitemap,
    "categories": CategorySitemap,
    "brands": BrandSitemap,
    "blog": BlogPostSitemap,
    "pages": StaticPageSitemap,
    "seo-landings": SeoLandingPageSitemap,
}
