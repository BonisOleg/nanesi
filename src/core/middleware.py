"""Українська мова лише для адмінки. Cookie мови вітрини не змінюється."""
from django.conf import settings
from django.utils import translation


class AdminUkrainianLocaleMiddleware:
    """Після LocaleMiddleware: адмінка завжди uk, вітрина лишається як є."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if _is_admin_path(request.path):
            translation.activate("uk")
            request.LANGUAGE_CODE = "uk"
        return self.get_response(request)


def _is_admin_path(path: str) -> bool:
    raw = str(settings.ADMIN_URL).strip()
    if not raw:
        return False
    if not raw.startswith("/"):
        raw = "/" + raw
    if not raw.endswith("/"):
        raw += "/"
    normalized = path if path.endswith("/") else path + "/"
    return normalized.startswith(raw)
