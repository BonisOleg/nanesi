from django.test import TestCase

from src.shipping.models import NPCity, NPWarehouse
from src.shipping.selectors import search_warehouses


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
