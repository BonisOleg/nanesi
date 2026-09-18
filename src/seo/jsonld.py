"""JSON-LD для Organization / Product / BreadcrumbList."""
import json
from decimal import Decimal

from django.conf import settings
from django.utils.translation import get_language, gettext as _

from src.seo.utils import absolute_url, localized_absolute_url


def dumps_ld(payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return raw.replace("<", "\\u003c")


def organization_payload(request, site) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": site.site_name,
        "url": absolute_url(request, "/"),
    }
    if site.logo:
        data["logo"] = absolute_url(request, site.logo.url)
    if site.email:
        data["email"] = site.email
    if site.phone:
        data["telephone"] = site.phone
    if site.address:
        data["address"] = {
            "@type": "PostalAddress",
            "addressLocality": site.address,
            "addressCountry": "UA",
        }
    same_as = [url for url in (site.instagram_url,) if url]
    if same_as:
        data["sameAs"] = same_as
    return data


def product_payload(request, product, variant=None) -> dict:
    variant = variant or getattr(product, "default_variant", None)
    lang = get_language() or settings.LANGUAGE_CODE
    description = (
        (getattr(product, "seo_description", None) or "")
        or product.short_description
        or product.description
        or product.name
    )
    images = []
    for image in product.images.all():
        images.append(absolute_url(request, image.image.url))
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.name,
        "description": description,
        "url": localized_absolute_url(request, product.get_absolute_url(), lang),
        "brand": {"@type": "Brand", "name": product.brand.name},
    }
    if images:
        data["image"] = images
    if variant:
        data["sku"] = variant.sku
        if variant.barcode:
            data["gtin"] = variant.barcode
        price = variant.current_price
        if isinstance(price, Decimal):
            price = format(price, "f")
        data["offers"] = {
            "@type": "Offer",
            "url": data["url"],
            "priceCurrency": "UAH",
            "price": str(price),
            "availability": (
                "https://schema.org/InStock"
                if variant.in_stock
                else "https://schema.org/OutOfStock"
            ),
            "itemCondition": "https://schema.org/NewCondition",
        }
    return data


def breadcrumbs_payload(request, items: list[tuple[str, str]]) -> dict:
    lang = get_language() or settings.LANGUAGE_CODE
    elements = []
    for index, (name, path) in enumerate(items, start=1):
        elements.append({
            "@type": "ListItem",
            "position": index,
            "name": name,
            "item": localized_absolute_url(request, path, lang),
        })
    if not elements:
        elements.append({
            "@type": "ListItem",
            "position": 1,
            "name": _("Головна"),
            "item": localized_absolute_url(request, "/", lang),
        })
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": elements,
    }
