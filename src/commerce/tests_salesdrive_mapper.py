"""Тести мапінгу сайту → SalesDrive (знижка промокоду в costPerItem)."""
from decimal import Decimal
from unittest import TestCase

from src.commerce.salesdrive_mapper import (
    build_create_payload,
    comment_with_promo,
    discounted_unit_prices,
)


class DiscountedUnitPricesTests(TestCase):
    def test_no_discount_keeps_prices(self):
        items = [
            {"unit_price": "1000.00", "qty": 1},
            {"unit_price": "500.00", "qty": 2},
        ]
        prices = discounted_unit_prices(items, 0)
        self.assertEqual(prices, [Decimal("1000.00"), Decimal("500.00")])

    def test_percent_like_proportional_single_item(self):
        items = [{"unit_price": "2390.00", "qty": 1}]
        prices = discounted_unit_prices(items, Decimal("239.00"))
        self.assertEqual(prices, [Decimal("2151.00")])

    def test_proportional_two_items_sum_matches(self):
        items = [
            {"unit_price": "1000.00", "qty": 1},
            {"unit_price": "500.00", "qty": 2},
        ]
        # subtotal 2000, discount 200 → target 1800
        prices = discounted_unit_prices(items, Decimal("200.00"))
        total = prices[0] * 1 + prices[1] * 2
        self.assertEqual(total, Decimal("1800.00"))
        # 1000/2000 * 200 = 100 → 900; 1000/2000 * 200 = 100 → 900/2 = 450
        self.assertEqual(prices[0], Decimal("900.00"))
        self.assertEqual(prices[1], Decimal("450.00"))


class CommentWithPromoTests(TestCase):
    def test_empty_without_discount(self):
        self.assertEqual(comment_with_promo({"comment": "Hi", "discount_amount": 0}), "Hi")

    def test_appends_promo_line(self):
        text = comment_with_promo({
            "comment": "Терміново",
            "promo_code": "WELCOME10",
            "discount_amount": "158.90",
        })
        self.assertEqual(text, "Терміново\nПромокод: WELCOME10, знижка: 158.90 грн")

    def test_promo_only_comment(self):
        text = comment_with_promo({
            "promo_code": "SALE",
            "discount_amount": "10",
        })
        self.assertEqual(text, "Промокод: SALE, знижка: 10.00 грн")


class BuildCreatePayloadDiscountTests(TestCase):
    def test_products_use_final_unit_price_and_promo_in_comment(self):
        body = build_create_payload({
            "full_name": "Test User",
            "phone": "+380501112233",
            "email": "t@example.com",
            "number": "N-1",
            "comment": "",
            "payment_method": "cod",
            "delivery_method": "np_warehouse",
            "promo_code": "MINUS10",
            "discount_amount": "239.00",
            "items": [
                {
                    "name": "Крем",
                    "sku": "EYE-1",
                    "qty": 1,
                    "unit_price": "2390.00",
                },
            ],
        })
        self.assertEqual(body["products"][0]["costPerItem"], 2151.0)
        self.assertIn("Промокод: MINUS10, знижка: 239.00 грн", body["comment"])
