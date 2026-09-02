"""Вимкнення ru/en з адмінки + захист від зламаних /ru/en/ URL."""
from django.conf import settings
from django.shortcuts import redirect

from src.core.views_i18n import collapse_double_prefix, localize_path


class DisabledLanguageRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        collapsed = collapse_double_prefix(request.get_full_path())
        if collapsed != request.get_full_path():
            return redirect(collapsed)

        lang = getattr(request, "LANGUAGE_CODE", None)
        if lang and lang != settings.LANGUAGE_CODE and not self._is_enabled(lang):
            return redirect(localize_path(request.get_full_path(), settings.LANGUAGE_CODE))
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
