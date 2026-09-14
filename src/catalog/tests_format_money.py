from decimal import Decimal

from django.test import SimpleTestCase
from django.utils import translation

from src.catalog.templatetags.shop_extras import currency_label, format_money


class FormatMoneyTests(SimpleTestCase):
    def test_uk_uses_grn(self):
        with translation.override("uk"):
            self.assertEqual(currency_label(), "грн")
            self.assertEqual(format_money(Decimal("1290")), "1 290\xa0грн")
            self.assertEqual(format_money(Decimal("1290.50")), "1 290.50\xa0грн")

    def test_en_uses_uah(self):
        with translation.override("en"):
            self.assertEqual(currency_label(), "UAH")
            self.assertEqual(format_money(Decimal("1290")), "1 290\xa0UAH")

    def test_ru_uses_grn(self):
        with translation.override("ru"):
            self.assertEqual(format_money(Decimal("100")), "100\xa0грн")
