from unittest.mock import patch

import requests
from django.test import TestCase, override_settings
from django.urls import reverse

from src.shipping.client import NovaPoshtaClient, NovaPoshtaError
from src.shipping.models import NPCity, NPWarehouse
from src.shipping.selectors import search_cities, search_warehouses


class NPCitySearchTests(TestCase):
    def test_kyiv_ranks_above_oblast_substring_matches(self):
        """«киї» має віддати Київ раніше за села з «Київська» у назві."""
        NPCity.objects.create(ref="a1", name="Андріївка (Київська обл.)", area="Київська")
        NPCity.objects.create(ref="a2", name="Антонівка (Київська обл.)", area="Київська")
        NPCity.objects.create(ref="kyiv", name="Київ", area="Київська")
        NPCity.objects.create(ref="kyivka", name="Київка", area="Полтавська")

        names = [c.name for c in search_cities("киї")]
        self.assertEqual(names[0], "Київ")
        self.assertIn("Київка", names)
        self.assertLess(names.index("Київ"), names.index("Київка"))
        self.assertLess(names.index("Київка"), names.index("Андріївка (Київська обл.)"))

    def test_city_search_returns_all_matches_without_cap(self):
        for i in range(35):
            NPCity.objects.create(ref=f"c-{i}", name=f"Тестмісто {i:02d}")
        self.assertEqual(len(list(search_cities("тестмісто"))), 35)

    def test_typographic_apostrophe_finds_kamianets(self):
        """НП зберігає ASCII ', користувач часто вводить ’ (U+2019) або ʼ (U+02BC)."""
        NPCity.objects.create(ref="kp", name="Кам'янець-Подільський", area="Хмельницька")
        for query in ("Кам\u2019янець", "Кам\u02bcянець"):
            with self.subTest(query=query):
                names = [city.name for city in search_cities(query)]
                self.assertIn("Кам'янець-Подільський", names)


class NPWarehouseDisplayTests(TestCase):
    def setUp(self):
        self.city = NPCity.objects.create(ref="city-1", name="Київ")

    def test_postomat_gets_label_when_missing_in_description(self):
        point = NPWarehouse.objects.create(
            ref="p-1", city=self.city, number="1",
            description="вул. Хрещатик, 1", category="Postomat",
        )
        self.assertTrue(point.is_postomat)
        self.assertIn("Поштомат", point.display_name())

    def test_postomat_does_not_duplicate_label(self):
        point = NPWarehouse.objects.create(
            ref="p-2", city=self.city, number="2",
            description="Поштомат №2: вул. Хрещатик, 2", category="Postomat",
        )
        self.assertEqual(point.display_name(), "Поштомат №2: вул. Хрещатик, 2")

    def test_search_excludes_cargo_and_lists_postomats_after_branches(self):
        NPWarehouse.objects.create(
            ref="c-1", city=self.city, number="90",
            description="Вантажне", category="Cargo",
        )
        NPWarehouse.objects.create(
            ref="b-1", city=self.city, number="12",
            description="Відділення №12", category="Branch",
        )
        NPWarehouse.objects.create(
            ref="p-3", city=self.city, number="3",
            description="Поштомат №3", category="Postomat",
        )
        results = list(search_warehouses(self.city.pk))
        refs = [row.ref for row in results]
        self.assertEqual(refs, ["b-1", "p-3"])

    def test_numeric_query_ranks_exact_number_first(self):
        NPWarehouse.objects.create(
            ref="b-112", city=self.city, number="112",
            description="Відділення №112 (до 10 кг)", category="Branch",
        )
        NPWarehouse.objects.create(
            ref="b-12", city=self.city, number="12",
            description="Відділення №12: вул. Родини Бунге, 8", category="Branch",
        )
        NPWarehouse.objects.create(
            ref="b-10212", city=self.city, number="10212",
            description="Пункт №10212", category="Branch",
        )
        refs = [row.ref for row in search_warehouses(self.city.pk, "12")]
        self.assertEqual(refs[0], "b-12")
        self.assertLess(refs.index("b-12"), refs.index("b-112"))

    def test_warehouse_suggestions_are_capped(self):
        for i in range(55):
            NPWarehouse.objects.create(
                ref=f"b-{i}", city=self.city, number=str(i),
                description=f"Відділення №{i}", category="Branch",
            )
        self.assertEqual(len(list(search_warehouses(self.city.pk))), 40)
        self.assertEqual(len(list(search_warehouses(self.city.pk, limit=None))), 55)


@override_settings(NP_API_KEY="test-only-np-key")
class NPWarehousesTimeoutTests(TestCase):
    def test_timeout_without_warehouses_returns_unavailable(self):
        city = NPCity.objects.create(ref="empty-city", name="Порожнє")
        with patch("src.shipping.client.requests.post", side_effect=requests.Timeout("timeout")):
            response = self.client.get(reverse("shipping:np_warehouses"), {"city": city.pk})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"configured": True, "results": [], "error": "np_unavailable"},
        )

    def test_timeout_with_warehouses_returns_cached(self):
        """Порожня category змушує повторний синк: таймаут не має ховати вже збережені відділення."""
        city = NPCity.objects.create(ref="cached-city", name="Київ")
        NPWarehouse.objects.create(
            ref="w-cached", city=city, number="5",
            description="Відділення №5", category="",
        )
        with patch("src.shipping.client.requests.post", side_effect=requests.Timeout("timeout")) as post:
            response = self.client.get(reverse("shipping:np_warehouses"), {"city": city.pk})
        self.assertTrue(post.called)
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["configured"])
        self.assertEqual([row["ref"] for row in payload["results"]], ["w-cached"])
        self.assertNotIn("error", payload)


class NovaPoshtaClientCallTests(TestCase):
    def test_call_wraps_timeout_into_nova_poshta_error(self):
        client = NovaPoshtaClient("test-key")
        with patch("src.shipping.client.requests.post", side_effect=requests.Timeout("timeout")) as post:
            with self.assertLogs("src.shipping.client", level="WARNING"):
                with self.assertRaises(NovaPoshtaError):
                    client.call("Address", "getWarehouses", {"CityRef": "city-ref"})
        self.assertEqual(post.call_args.kwargs["timeout"], (5, 10))
