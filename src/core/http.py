"""Безпечні редіректи після логіну / wishlist."""
from django.utils.http import url_has_allowed_host_and_scheme


def safe_next(request, fallback: str = "/") -> str:
    candidates = (
        request.POST.get("next") or "",
        request.GET.get("next") or "",
        request.META.get("HTTP_REFERER") or "",
    )
    host = request.get_host()
    require_https = request.is_secure()
    for raw in candidates:
        raw = (raw or "").strip()
        if not raw:
            continue
        if url_has_allowed_host_and_scheme(
            raw, allowed_hosts={host}, require_https=require_https,
        ):
            return raw
    return fallback
