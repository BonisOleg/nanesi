"""Фільтр «Країна виробник» у списку товарів і SEO-підписи форми товару."""
import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_str

from src.catalog.models import Attribute, AttributeValue, Brand, Category, Product
from src.seo.models import SeoLandingPage

SEO_TITLE = "SEO-заголовок (title)"
SEO_DESCRIPTION = "SEO-опис (description)"
SEO_KEYWORDS = "Ключові слова (keywords)"
SEO_TITLE_HELP = "Заголовок сторінки для пошукових систем, до ~60 символів"
SEO_DESCRIPTION_HELP = "Опис сторінки у видачі пошукових систем, до ~160 символів"


class CountryProducerFilterTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser("country-admin", "country@example.com", "pass-word-1")
        self.client.force_login(self.user)
        self.brand = Brand.objects.create(name="Бренд країни", slug="brand-country")
        self.category = Category.objects.create(name="Категорія країни", slug="cat-country")
        attribute = Attribute.objects.create(code="country", name="Країна / напрям", sort_order=30)
        self.japan = AttributeValue.objects.create(
            attribute=attribute, value="Японія", sort_order=1,
        )
        self.austria = AttributeValue.objects.create(
            attribute=attribute, value="Австрія", sort_order=2,
        )
        self.japan_product = self._product("Товар Японія", "prod-japan", [self.japan])
        self.austria_product = self._product("Товар Австрія", "prod-austria", [self.austria])
        self.both_product = self._product("Товар обидві країни", "prod-both", [self.japan, self.austria])
        self.plain_product = self._product("Товар без країни", "prod-plain", [])
        self.url = reverse("admin:catalog_product_changelist")

    def _product(self, name, slug, values):
        product = Product.objects.create(
            name=name,
            slug=slug,
            brand=self.brand,
            category=self.category,
        )
        if values:
            product.attribute_values.add(*values)
        return product

    def test_country_select_lists_all_and_values_in_sort_order(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        positions = [
            html.find(f'<span class="admin-top-filters__label">{label}</span>')
            for label in ("Категорія", "Бренд", "Країна виробник")
        ]
        self.assertTrue(all(pos >= 0 for pos in positions))
        self.assertLess(positions[0], positions[1])
        self.assertLess(positions[1], positions[2])

        start = positions[2]
        chunk = html[start:html.find("</select>", start)]
        labels = re.findall(r"<option[^>]*>(.*?)</option>", chunk)
        self.assertEqual(labels, ["Усі", "Японія", "Австрія"])

    def test_country_filter_returns_matching_products_once(self):
        response = self.client.get(self.url, {"country": self.japan.pk})
        self.assertEqual(response.status_code, 200)
        cl = response.context["cl"]
        ids = [obj.pk for obj in cl.result_list]
        self.assertEqual(cl.result_count, 2)
        self.assertEqual(len(ids), 2)
        self.assertCountEqual(ids, [self.japan_product.pk, self.both_product.pk])
        self.assertEqual(ids.count(self.both_product.pk), 1)
        self.assertNotIn(self.austria_product.pk, ids)
        self.assertNotIn(self.plain_product.pk, ids)

        austria = self.client.get(self.url, {"country": self.austria.pk})
        austria_ids = [obj.pk for obj in austria.context["cl"].result_list]
        self.assertEqual(austria.context["cl"].result_count, 2)
        self.assertCountEqual(austria_ids, [self.austria_product.pk, self.both_product.pk])
        self.assertEqual(austria_ids.count(self.both_product.pk), 1)

    def test_invalid_country_param_is_empty(self):
        response = self.client.get(self.url, {"country": "nope"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["cl"].result_count, 0)

    def test_product_form_has_ukrainian_seo_labels(self):
        for model, title_fields, description_fields, keyword_fields in (
            (
                Product,
                ("seo_title", "seo_title_uk", "seo_title_ru", "seo_title_en"),
                ("seo_description", "seo_description_uk", "seo_description_ru", "seo_description_en"),
                ("seo_keywords", "seo_keywords_uk", "seo_keywords_ru", "seo_keywords_en"),
            ),
            (
                SeoLandingPage,
                ("meta_title", "meta_title_uk", "meta_title_ru", "meta_title_en"),
                ("meta_description", "meta_description_uk", "meta_description_ru", "meta_description_en"),
                (),
            ),
        ):
            for name in title_fields:
                field = model._meta.get_field(name)
                self.assertIn(SEO_TITLE, force_str(field.verbose_name))
                self.assertEqual(force_str(field.help_text), SEO_TITLE_HELP)
            for name in description_fields:
                field = model._meta.get_field(name)
                self.assertIn(SEO_DESCRIPTION, force_str(field.verbose_name))
                self.assertEqual(force_str(field.help_text), SEO_DESCRIPTION_HELP)
            for name in keyword_fields:
                self.assertIn(SEO_KEYWORDS, force_str(model._meta.get_field(name).verbose_name))

        url = reverse("admin:catalog_product_change", args=[self.japan_product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, SEO_TITLE)
        self.assertContains(response, SEO_DESCRIPTION)
        self.assertContains(response, SEO_KEYWORDS)
        self.assertContains(response, SEO_TITLE_HELP)
        self.assertContains(response, SEO_DESCRIPTION_HELP)
        self.assertNotContains(response, "SEO title")
        self.assertNotContains(response, "SEO description")
        self.assertNotContains(response, "SEO keywords")


class CountryFilterHiddenWithoutValuesTests(TestCase):
    def test_filter_hidden_when_country_attribute_missing(self):
        User = get_user_model()
        user = User.objects.create_superuser("nocountry", "nocountry@example.com", "pass-word-1")
        self.client.force_login(user)
        brand = Brand.objects.create(name="Бренд без країни", slug="brand-no-country")
        category = Category.objects.create(name="Категорія без країни", slug="cat-no-country")
        Product.objects.create(name="Без атрибута", slug="prod-no-attr", brand=brand, category=category)
        response = self.client.get(reverse("admin:catalog_product_changelist"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Країна виробник")
