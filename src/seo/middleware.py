"""www.nanesi.com.ua → nanesi.com.ua. IP / localhost не чіпає."""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect

from src.seo.utils import public_scheme


class CanonicalHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        canonical = (getattr(settings, "CANONICAL_HOST", "") or "").strip().lower()
        if not canonical:
            return self.get_response(request)
        host = (request.get_host() or "").split(":")[0].lower()
        if host != f"www.{canonical}":
            return self.get_response(request)
        target = f"{public_scheme(request)}://{canonical}{request.get_full_path()}"
        return HttpResponsePermanentRedirect(target)
