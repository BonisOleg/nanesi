from django.test import TestCase

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
