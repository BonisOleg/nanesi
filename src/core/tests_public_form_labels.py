"""Публічні підписи форм лишаються такими, як до українських verbose_name адмінки."""
from django.test import TestCase
from django.utils.html import conditional_escape
from django.utils.translation import override

from src.accounts.forms import LoginForm, ProfileForm, RegisterForm, SavedWarehouseForm
from src.catalog.forms import ReviewForm
from src.commerce.forms import CheckoutForm


def _same(text):
    return {"uk": text, "ru": text, "en": text}


def _pack(fields):
    packed = {lang: {} for lang in ("uk", "ru", "en")}
    for name, labels in fields.items():
        for lang, text in labels.items():
            packed[lang][name] = text
    return packed


EXPECTED = {
    "login": _pack({
        "username": {"uk": "Телефон або email", "ru": "Телефон или email", "en": "Phone or email"},
        "password": {"uk": "Пароль", "ru": "Пароль", "en": "Password"},
    }),
    "register": _pack({
        "full_name": {"uk": "Ім'я", "ru": "Имя", "en": "Name"},
        "phone": {"uk": "Телефон", "ru": "Телефон", "en": "Phone"},
        "email": _same("Email"),
        "password1": {"uk": "Пароль", "ru": "Пароль", "en": "Password"},
        "password2": {"uk": "Повторіть пароль", "ru": "Повторите пароль", "en": "Repeat password"},
    }),
    "profile": _pack({
        "first_name": {"uk": "Ім'я", "ru": "Имя", "en": "Name"},
        "last_name": {"uk": "Прізвище", "ru": "Фамилия", "en": "Last name"},
        "phone": {"uk": "Телефон", "ru": "Телефон", "en": "Phone"},
        "email": _same("Email"),
    }),
    "warehouse": _pack({
        "saved_np_city_name": {"uk": "Місто", "ru": "Город", "en": "City"},
        "saved_np_warehouse_name": {
            "uk": "Відділення / поштомат",
            "ru": "Отделение / почтомат",
            "en": "Branch / postomat",
        },
        "saved_ukrposhta_index": {
            "uk": "Індекс Укрпошти",
            "ru": "Индекс Укрпочты",
            "en": "Ukrposhta postal code",
        },
        "saved_ukrposhta_address": {
            "uk": "Адреса / відділення Укрпошти",
            "ru": "Адрес / отделение Укрпочты",
            "en": "Ukrposhta address / branch",
        },
        "saved_np_city_ref": _same("Ref міста (НП)"),
        "saved_np_warehouse_ref": _same("Ref відділення / поштомату (НП)"),
    }),
    "checkout": _pack({
        "full_name": _same("ПІБ"),
        "phone": _same("Телефон"),
        "email": _same("Email"),
        "delivery_method": _same("Спосіб доставки"),
        "np_city_name": _same("Місто"),
        "np_warehouse_name": {
            "uk": "Відділення / поштомат",
            "ru": "Отделение / почтомат",
            "en": "Branch / postomat",
        },
        "ukrposhta_index": {"uk": "Індекс", "ru": "Индекс", "en": "Postal code"},
        "ukrposhta_address": _same("Адреса (Укрпошта)"),
        "payment_method": _same("Спосіб оплати"),
        "comment": _same("Коментар"),
        "privacy_consent": {
            "uk": "Згода на обробку персональних даних",
            "ru": "Согласие на обработку персональных данных",
            "en": "Consent to personal data processing",
        },
    }),
    "review": _pack({
        "author_name": {"uk": "Ваше ім'я", "ru": "Ваше имя", "en": "Your name"},
        "rating": {"uk": "Оцінка", "ru": "Оценка", "en": "Rating"},
        "text": {"uk": "Текст відгуку", "ru": "Текст отзыва", "en": "Review text"},
        "photos": {"uk": "Фото (до 5)", "ru": "Фото (до 5)", "en": "Photos (up to 5)"},
    }),
}


class PublicFormLabelTests(TestCase):
    def _build(self):
        return {
            "login": LoginForm(),
            "register": RegisterForm(),
            "profile": ProfileForm(),
            "warehouse": SavedWarehouseForm(),
            "checkout": CheckoutForm(),
            "review": ReviewForm(),
        }

    def test_labels_stay_pre_admin_wording_in_uk_ru_en(self):
        for language in ("uk", "ru", "en"):
            with override(language):
                forms = self._build()
                for form_name, expected in EXPECTED.items():
                    form = forms[form_name]
                    for field_name, label in expected[language].items():
                        actual = str(form[field_name].label)
                        rendered = str(form[field_name].label_tag())
                        self.assertEqual(
                            actual,
                            label,
                            f"{form_name}.{field_name} [{language}]",
                        )
                        self.assertIn(str(conditional_escape(label)), rendered)
