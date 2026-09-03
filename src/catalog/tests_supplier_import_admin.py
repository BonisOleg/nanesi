"""Видимість кнопки «Імпорт прайсу» в Unfold-адмінці."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from src.catalog.models import Supplier


class SupplierImportAdminVisibilityTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser("admin", "a@b.c", "pass")
        self.supplier = Supplier.objects.create(name="Cosmetics Factory")
        self.client.force_login(self.user)

    def test_import_url_resolves_and_shows_examples(self):
        url = reverse("admin:catalog_supplier_import_price", args=[self.supplier.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "pryklad-praisu.csv")
        self.assertContains(response, "pryklad-praisu.xlsx")
        self.assertContains(response, "Завантажити приклад")
        self.assertContains(response, "Приклад CSV")
        self.assertContains(response, "Приклад XLSX")
        self.assertContains(response, "закупівельна")

    def test_change_form_shows_import_action(self):
        url = reverse("admin:catalog_supplier_change", args=[self.supplier.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Імпорт прайсу")
        self.assertContains(response, f"{self.supplier.pk}/import/")

    def test_changelist_row_shows_import_action(self):
        url = reverse("admin:catalog_supplier_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Імпорт прайсу")
        self.assertContains(response, f"{self.supplier.pk}/import")
