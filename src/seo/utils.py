"""Канонічний host, hreflang і noindex для вітрини (uk без префікса)."""
from django.conf import settings
from django.utils.translation import get_language

from src.core.views_i18n import localize_path, strip_language_prefix

OG_LOCALES = {"uk": "uk_UA", "ru": "ru_RU", "en": "en_US"}

_PRIVATE_PREFIXES = (
    "/kabinet/",
    "/koshyk/",
    "/oformlennya/",
    "/obrane/",
    "/i18n/",
    "/admin/",
)
_FACET_QUERY_KEYS = frozenset({
    "skin_type",
    "concern",
    "country",
    "ingredient",
    "age",
    "spf",
    "brand",
    "category",
    "volume",
    "stock",
    "sale",
    "price_min",
    "price_max",
    "sort",
})
def enabled_language_codes(site=None) -> list[str]:
    if site is None:
        from src.content.models import SiteSettings

        site = SiteSettings.load()
    codes = [settings.LANGUAGE_CODE]
    if site.ru_enabled:
        codes.append("ru")
    if site.en_enabled:
        codes.append("en")
    return codes


def language_neutral_path(path: str) -> str:
    return strip_language_prefix(path or "/").split("?", 1)[0] or "/"


def public_host(request) -> str:
    configured = (getattr(settings, "CANONICAL_HOST", "") or "").strip().lower()
    current = (request.get_host() or "").split(":")[0].lower()
    if configured and current in {configured, f"www.{configured}"}:
        return configured
    return request.get_host()


def public_scheme(request) -> str:
    host = public_host(request)
    configured = (getattr(settings, "CANONICAL_HOST", "") or "").strip().lower()
    if getattr(settings, "USE_HTTPS", False) and configured and host == configured:
        return "https"
    if request.is_secure():
        return "https"
    return "http"


def absolute_url(request, path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return f"{public_scheme(request)}://{public_host(request)}{path}"


def localized_absolute_url(request, path: str, lang: str | None = None) -> str:
    lang = lang or (get_language() or settings.LANGUAGE_CODE)
    return absolute_url(request, localize_path(language_neutral_path(path), lang))


def is_search_path(path: str) -> bool:
    clean = language_neutral_path(path).rstrip("/")
    return clean == "/poshuk" or clean.startswith("/poshuk/")


def is_private_path(path: str) -> bool:
    clean = language_neutral_path(path)
    if not clean.endswith("/"):
        clean = clean + "/"
    return any(clean.startswith(prefix) for prefix in _PRIVATE_PREFIXES)


def should_noindex(request) -> bool:
    path = request.path
    if is_search_path(path) or is_private_path(path):
        return True
    if request.GET.get("page", "1") not in {"", "1"}:
        return True
    if any(key in request.GET for key in _FACET_QUERY_KEYS):
        return True
    return False


def canonical_path(request) -> str:
    lang = get_language() or settings.LANGUAGE_CODE
    if is_search_path(request.path):
        return localize_path("/katalog/", lang)
    return localize_path(language_neutral_path(request.path), lang)


def hreflang_map(request) -> dict[str, str]:
    path = language_neutral_path(request.path)
    if is_search_path(request.path):
        path = "/katalog/"
    urls = {
        code: absolute_url(request, localize_path(path, code))
        for code in enabled_language_codes()
    }
    if "uk" in urls:
        urls["x-default"] = urls["uk"]
    return urls


def og_locale(lang: str | None = None) -> str:
    code = (lang or get_language() or "uk").split("-")[0]
    return OG_LOCALES.get(code, "uk_UA")


def default_og_image_url(request, site=None) -> str:
    if site is None:
        from src.content.models import SiteSettings

        site = SiteSettings.load()
    for field in ("logo", "hero_image"):
        image = getattr(site, field, None)
        if image:
            return absolute_url(request, image.url)
    return ""
