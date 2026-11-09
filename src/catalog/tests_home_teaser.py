"""Описи промо-карток на головній — з адмінки (Collection.home_teaser)."""
from django.test import TestCase
from django.urls import reverse
from django.utils import translation

from src.catalog.models import Category, Collection


class HomeTeaserTests(TestCase):
    def setUp(self):
        Category.objects.create(name="Сироватки", slug="syrovatky", is_active=True)

    def test_custom_teaser_rendered_and_test_phrase_gone(self):
        Collection.objects.create(
            name="Акції",
            slug="aktsii",
            kind=Collection.Kind.SALE,
            home_teaser="Спеціальні ціни цього тижня.",
            is_active=True,
            sort_order=1,
        )
        with translation.override("uk"):
            response = self.client.get(reverse("catalog:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Спеціальні ціни цього тижня.")
        self.assertNotContains(response, "тестового асортименту")

    def test_empty_teaser_uses_kind_default_without_test_phrase(self):
        Collection.objects.create(
            name="Акції",
            slug="aktsii",
            kind=Collection.Kind.SALE,
            home_teaser="",
            is_active=True,
            sort_order=1,
        )
        with translation.override("uk"):
            response = self.client.get(reverse("catalog:home"))
        self.assertContains(response, "Акційні позиції.")
        self.assertNotContains(response, "тестового асортименту")
