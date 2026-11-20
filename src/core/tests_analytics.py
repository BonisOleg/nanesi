from types import SimpleNamespace

from django.test import TestCase

from src.core.analytics import phone_to_e164, should_track_purchase, user_data_from_contact


class PhoneE164Tests(TestCase):
    def test_plus380(self):
        self.assertEqual(phone_to_e164("+380991234567"), "+380991234567")

    def test_leading_zero(self):
        self.assertEqual(phone_to_e164("0991234567"), "+380991234567")

    def test_bare_380(self):
        self.assertEqual(phone_to_e164("380991234567"), "+380991234567")

    def test_nine_digits(self):
        self.assertEqual(phone_to_e164("991234567"), "+380991234567")


class PurchaseGateTests(TestCase):
    def test_card_unpaid_skipped(self):
        order = SimpleNamespace(payment_method="card_online", payment_status="unpaid")
        self.assertFalse(should_track_purchase(order))

    def test_card_paid_tracked(self):
        order = SimpleNamespace(payment_method="card_online", payment_status="paid")
        self.assertTrue(should_track_purchase(order))

    def test_cod_tracked(self):
        order = SimpleNamespace(payment_method="cod", payment_status="unpaid")
        self.assertTrue(should_track_purchase(order))


class UserDataTests(TestCase):
    def test_email_and_phone(self):
        data = user_data_from_contact(email="  a@b.c  ", phone="0501112233")
        self.assertEqual(data["email"], "a@b.c")
        self.assertEqual(data["phone_number"], "+380501112233")
