"""Canonical, hreflang, noindex, sitemap languages, www→apex."""
from decimal import Decimal

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Brand, Category, Collection, Product, ProductVariant
from src.content.models import SiteSettings


class SeoFixturesMixin:
    def setUp(self):
        translation.activate("uk")
        self.client.cookies.pop("django_language", None)
        self.brand = Brand.objects.create(name="SeoBrand", slug="seo-brand")
        self.category = Category.objects.create(name="SeoCat", slug="seo-cat")
        self.product = Product.objects.create(
            name="Serum SEO",
            slug="serum-seo",
            brand=self.brand,
            category=self.category,
            is_active=True,
            seo_title_uk="Сироватка SEO title",
            seo_description_uk="Опис для снипета",
            short_description="Короткий опис товару",
        )
        ProductVariant.objects.create(
            product=self.product,
            sku="SEO-SKU-1",
            retail_price=Decimal("199.00"),
            stock_quantity=4,
            is_active=True,
        )
        Collection.objects.create(name="Хіти", slug="hity-seo", is_active=True)

    def tearDown(self):
        translation.activate("uk")
        self.client.cookies.pop("django_language", None)


class StorefrontSeoTests(SeoFixturesMixin, TestCase):
    def test_home_has_canonical_hreflang_and_organization(self):
        response = self.client.get(reverse("catalog:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, 'hreflang="uk"')
        self.assertContains(response, 'hreflang="ru"')
        self.assertContains(response, 'hreflang="en"')
        self.assertContains(response, 'hreflang="x-default"')
        self.assertContains(response, 'property="og:title"')
        self.assertContains(response, '"@type":"Organization"')
        self.assertNotContains(response, "noindex")

    def test_ru_home_hreflang_points_to_apex_and_prefixed(self):
        response = self.client.get("/ru/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('hreflang="uk" href="http://testserver/"', content)
        self.assertIn('hreflang="ru" href="http://testserver/ru/"', content)
        self.assertIn('hreflang="x-default" href="http://testserver/"', content)
        self.assertIn('rel="canonical" href="http://testserver/ru/"', content)

    def test_search_is_noindex_canonical_to_catalog(self):
        response = self.client.get("/poshuk/", {"q": "serum"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="robots" content="noindex,follow"')
        self.assertContains(response, 'rel="canonical" href="http://testserver/katalog/"')

    def test_filtered_catalog_is_noindex_clean_canonical(self):
        response = self.client.get(reverse("catalog:catalog"), {"skin_type": "suhа"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "noindex")
        self.assertContains(response, 'rel="canonical" href="http://testserver/katalog/"')

    def test_pdp_uses_seo_fields_and_product_jsonld(self):
        response = self.client.get(self.product.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сироватка SEO title")
        self.assertContains(response, "Опис для снипета")
        self.assertContains(response, '"@type":"Product"')
        self.assertContains(response, "SEO-SKU-1")
        self.assertContains(response, '"@type":"BreadcrumbList"')
        self.assertContains(response, 'property="og:type" content="product"')

    def test_robots_disallows_search(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disallow: /poshuk/")
        self.assertContains(response, "Sitemap: http://testserver/sitemap.xml")

    def test_sitemap_includes_collection_and_product(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/tovar/serum-seo/")
        self.assertContains(response, "/dobirka/hity-seo/")
        self.assertContains(response, "/ru/tovar/serum-seo/")

    def test_sitemap_omits_disabled_language(self):
        site = SiteSettings.load()
        site.ru_enabled = False
        site.save(update_fields=["ru_enabled"])
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "/ru/tovar/serum-seo/")
        self.assertContains(response, "/en/tovar/serum-seo/")


class CanonicalHostTests(TestCase):
    @override_settings(
        CANONICAL_HOST="nanesi.com.ua",
        ALLOWED_HOSTS=["nanesi.com.ua", "www.nanesi.com.ua", "testserver"],
    )
    def test_www_redirects_to_apex(self):
        response = self.client.get("/katalog/?q=1", HTTP_HOST="www.nanesi.com.ua")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "http://nanesi.com.ua/katalog/?q=1")

    @override_settings(CANONICAL_HOST="nanesi.com.ua", ALLOWED_HOSTS=["46.101.212.242", "testserver"])
    def test_ip_host_is_not_redirected(self):
        response = self.client.get("/", HTTP_HOST="46.101.212.242")
        self.assertNotEqual(response.status_code, 301)
