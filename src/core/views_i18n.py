"""Надійний set_language без Django translate_url.

Канон для 3 мов (uk без префікса, ru/en з префіксом): next завжди проганяємо
через localize_path(lang) — прибрати будь-який /ru|/en і навісити цільовий.
Не використовуємо django.urls.translate_url (ламається з cookie + catch-all slug).
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.translation import check_for_language
from django.views.decorators.http import require_POST

_PREFIX_LANGS = frozenset(
    code for code, _ in settings.LANGUAGES if code != settings.LANGUAGE_CODE
)


def strip_language_prefix(path: str) -> str:
    """Прибрати всі провідні /ru|/en; зберегти query."""
    if not path:
        return "/"
    query = ""
    if "?" in path:
        path, query = path.split("?", 1)
        query = "?" + query
    changed = True
    while changed:
        changed = False
        for code in _PREFIX_LANGS:
            prefix = f"/{code}"
            if path == prefix or path == prefix + "/":
                path = "/"
                changed = True
                break
            if path.startswith(prefix + "/"):
                path = path[len(prefix) :] or "/"
                changed = True
                break
    if not path.startswith("/"):
        path = "/" + path
    return path + query


def localize_path(path: str, lang: str) -> str:
    """uk → без префікса; ru/en → /ru/... або /en/..."""
    path = strip_language_prefix(path or "/")
    if not path.startswith("/"):
        path = "/" + path
    if not lang or lang == settings.LANGUAGE_CODE or not check_for_language(lang):
        return path
    if path == "/":
        return f"/{lang}/"
    return f"/{lang}{path}"


def collapse_double_prefix(path: str) -> str:
    """/ru/en/foo → /en/foo."""
    query = ""
    if "?" in path:
        path, query = path.split("?", 1)
        query = "?" + query
    parts = [p for p in path.split("/") if p]
    while len(parts) >= 2 and parts[0] in _PREFIX_LANGS and parts[1] in _PREFIX_LANGS:
        parts.pop(0)
    if not parts:
        rebuilt = "/"
    elif parts[0] in _PREFIX_LANGS and len(parts) == 1:
        rebuilt = f"/{parts[0]}/"
    else:
        rebuilt = "/" + "/".join(parts) + ("/" if path.endswith("/") else "")
    return rebuilt + query


def _extract_next(request) -> str:
    raw = request.POST.get("next") or request.GET.get("next") or ""
    if raw.startswith("/") and not raw.startswith("//"):
        return raw
    if raw.startswith("http://") or raw.startswith("https://"):
        parts = urlsplit(raw)
        if parts.netloc == request.get_host():
            path = parts.path or "/"
            return f"{path}?{parts.query}" if parts.query else path
    referer = request.META.get("HTTP_REFERER") or ""
    if referer:
        parts = urlsplit(referer)
        if parts.netloc == request.get_host():
            path = parts.path or "/"
            return f"{path}?{parts.query}" if parts.query else path
    return "/"


@require_POST
def set_language(request):
    lang = (request.POST.get("language") or settings.LANGUAGE_CODE).strip()
    if not check_for_language(lang):
        lang = settings.LANGUAGE_CODE

    target = localize_path(_extract_next(request), lang)
    target = collapse_double_prefix(target)

    response = HttpResponseRedirect(target)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response
