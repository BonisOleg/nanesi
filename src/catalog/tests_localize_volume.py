"""Локалізація підписів об'єму (мл/г/рефіл) для вітрини."""
from django.test import SimpleTestCase
from django.utils import translation

from src.catalog.selectors import localize_volume_label


class LocalizeVolumeLabelTests(SimpleTestCase):
    def test_uk_unchanged(self):
        with translation.override("uk"):
            self.assertEqual(localize_volume_label("150 мл"), "150 мл")
            self.assertEqual(localize_volume_label("15 г + рефіл 15 г"), "15 г + рефіл 15 г")

    def test_en_units(self):
        with translation.override("en"):
            self.assertEqual(localize_volume_label("150 мл"), "150 ml")
            self.assertEqual(localize_volume_label("3.5 г"), "3.5 g")
            self.assertEqual(
                localize_volume_label("15 г + рефіл 15 г"),
                "15 g + refill 15 g",
            )

    def test_ru_refill(self):
        with translation.override("ru"):
            self.assertEqual(localize_volume_label("15 г + рефіл 15 г"), "15 г + рефил 15 г")
            self.assertEqual(localize_volume_label("60 мл"), "60 мл")
