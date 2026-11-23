"""Ліміт запитів по IP без Redis/DRF: Django cache (DatabaseCache у production)."""
from functools import wraps

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext as _


def client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    return (request.META.get("REMOTE_ADDR") or "unknown").strip()


def _hit_count(key: str, window: int) -> int:
    added = cache.add(key, 1, window)
    if added:
        return 1
    try:
        return int(cache.incr(key))
    except ValueError:
        cache.set(key, 1, window)
        return 1


def is_limited(request, *, scope: str, limit: int, window: int) -> bool:
    if not getattr(settings, "RATELIMIT_ENABLED", True):
        return False
    ip = client_ip(request)
    count = _hit_count(f"rl:{scope}:{ip}", window)
    return count > limit


def _too_many(request, retry_after: int):
    message = str(_("Забагато запитів. Спробуйте пізніше."))
    accept = request.headers.get("Accept") or ""
    wants_json = (
        "application/json" in accept
        or request.headers.get("X-Requested-With") == "fetch"
        or request.headers.get("HX-Request")
    )
    if wants_json:
        response = JsonResponse({"ok": False, "error": message}, status=429)
    else:
        response = HttpResponse(message, status=429, content_type="text/plain; charset=utf-8")
    response["Retry-After"] = str(retry_after)
    return response


def ratelimit(*, scope: str, limit: int, window: int, methods: tuple[str, ...] = ("POST",)):
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method in methods and is_limited(
                request, scope=scope, limit=limit, window=window,
            ):
                return _too_many(request, window)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator
