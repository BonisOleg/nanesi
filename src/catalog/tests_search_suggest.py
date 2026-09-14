from django.test import TestCase
from django.urls import reverse

from src.catalog.models import Brand, Category, Product, ProductVariant
from src.catalog.selectors import search_suggest


class SearchSuggestTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="Round Lab", slug="round-lab", is_active=True)
        self.category = Category.objects.create(name="Сироватки", slug="syrovatky", is_active=True)
        self.product = Product.objects.create(
            name="Centella Ampoule",
            slug="centella-ampoule",
            brand=self.brand,
            category=self.category,
            is_active=True,
        )
        ProductVariant.objects.create(
            product=self.product,
            sku="RL-CEN-30",
            retail_price="890.00",
            stock_quantity=5,
            is_active=True,
        )

    def test_suggest_by_name_brand_sku(self):
        self.assertEqual(len(search_suggest("ce")), 1)
        self.assertEqual(len(search_suggest("round")), 1)
        self.assertEqual(len(search_suggest("RL-CEN")), 1)
        self.assertEqual(search_suggest("x"), [])

    def test_endpoint_json(self):
        url = reverse("catalog:search_suggest")
        response = self.client.get(url, {"q": "centella"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["name"], "Centella Ampoule")
        self.assertEqual(payload["results"][0]["brand"], "Round Lab")
        self.assertTrue(payload["results"][0]["url"])
