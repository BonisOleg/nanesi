from decimal import Decimal

from django.test import TestCase

from src.commerce.selectors import format_uah_amount, free_shipping_progress
from src.content.models import SiteSettings


class FreeShippingProgressTests(TestCase):
    def setUp(self):
        site = SiteSettings.load()
        site.free_shipping_threshold = Decimal("1500.00")
        site.save(update_fields=["free_shipping_threshold"])

    def test_remaining_copy_values(self):
        progress = free_shipping_progress(Decimal("1200.00"))
        self.assertFalse(progress.reached)
        self.assertEqual(progress.remaining_display, "300")
        self.assertEqual(progress.percent, 80)

    def test_reached_at_threshold(self):
        progress = free_shipping_progress(Decimal("1500.00"))
        self.assertTrue(progress.reached)
        self.assertEqual(progress.percent, 100)
        self.assertEqual(progress.remaining_display, "0")

    def test_disabled_when_threshold_empty(self):
        site = SiteSettings.load()
        site.free_shipping_threshold = None
        site.save(update_fields=["free_shipping_threshold"])
        progress = free_shipping_progress(Decimal("2000.00"))
        self.assertIsNone(progress.threshold)
        self.assertFalse(progress.reached)

    def test_format_uah_amount(self):
        self.assertEqual(format_uah_amount(Decimal("300.00")), "300")
        self.assertEqual(format_uah_amount(Decimal("300.50")), "300,50")

    def test_promo_does_not_undo_free_shipping_progress(self):
        """Пороги рахуються від subtotal; знижка 1589→1430 не знімає reached."""
        progress = free_shipping_progress(Decimal("1589.00"))
        self.assertTrue(progress.reached)
        self.assertEqual(progress.percent, 100)


class PromoDiscountMoneyTests(TestCase):
    def test_percent_discount_two_decimals(self):
        from src.commerce.models import PromoCode

        promo = PromoCode(
            code="TEST10",
            discount_type=PromoCode.DiscountType.PERCENT,
            discount_value=Decimal("10"),
            is_active=True,
        )
        discount = promo.calculate_discount(Decimal("1589.00"))
        self.assertEqual(discount, Decimal("158.90"))
        self.assertEqual(str(discount), "158.90")
        total = Decimal("1589.00") - discount
        from src.commerce.models_1 import money

        self.assertEqual(money(total), Decimal("1430.10"))
        self.assertEqual(str(money(total)), "1430.10")
