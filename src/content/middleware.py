"""Вимкнення ru/en з адмінки без участі розробника (Доповнення §1 «Мови»).

LocaleMiddleware сам не знає про SiteSettings.ru_enabled/en_enabled — тут
перевіряємо вже визначену мову запиту і, якщо вона вимкнена, повертаємо той
самий шлях під основною (uk) мовою.
"""
from django.conf import settings
from django.shortcuts import redirect
from django.urls import translate_url


class DisabledLanguageRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        lang = getattr(request, "LANGUAGE_CODE", None)
        if lang and lang != settings.LANGUAGE_CODE and not self._is_enabled(lang):
            new_path = translate_url(request.get_full_path(), settings.LANGUAGE_CODE)
            return redirect(new_path)
        return self.get_response(request)

    @staticmethod
    def _is_enabled(lang: str) -> bool:
        from src.content.models import SiteSettings

        site_settings = SiteSettings.load()
        if lang == "ru":
            return site_settings.ru_enabled
        if lang == "en":
            return site_settings.en_enabled
        return True
