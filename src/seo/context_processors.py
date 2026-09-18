"""Canonical, hreflang, robots і дефолтні OG для кожного request."""
from django.utils.translation import get_language

from src.seo.utils import (
    absolute_url,
    canonical_path,
    default_og_image_url,
    hreflang_map,
    og_locale,
    should_noindex,
)


def seo(request):
    from src.content.models import SiteSettings

    site = SiteSettings.load()
    return {
        "seo_canonical": absolute_url(request, canonical_path(request)),
        "seo_hreflangs": hreflang_map(request),
        "seo_noindex": should_noindex(request),
        "seo_og_locale": og_locale(get_language()),
        "seo_og_image": default_og_image_url(request, site),
    }
