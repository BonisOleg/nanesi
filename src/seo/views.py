from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import SeoLandingPage


def render_landing(request: HttpRequest, page: SeoLandingPage) -> HttpResponse:
    """Рендер SEO-лендінга — викликається з catch-all у content/views.py."""
    products = page.products.filter(is_active=True)
    return render(request, "seo/landing_detail.html", {"page": page, "products": products})


def robots_txt(request: HttpRequest) -> HttpResponse:
    from src.seo.utils import absolute_url

    lines = [
        "User-agent: *",
        "Disallow: /kabinet/",
        "Disallow: /koshyk/",
        "Disallow: /oformlennya/",
        "Disallow: /admin/",
        "Disallow: /obrane/",
        "Disallow: /i18n/",
        "Disallow: /poshuk/",
        "Disallow: /ru/poshuk/",
        "Disallow: /en/poshuk/",
        "Disallow: /tovar/*/vidguk/",
        "",
        f"Sitemap: {absolute_url(request, '/sitemap.xml')}",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")
