from django import template

from src.seo.jsonld import breadcrumbs_payload, dumps_ld, organization_payload, product_payload

register = template.Library()


@register.inclusion_tag("seo/partials/_jsonld_script.html", takes_context=True)
def jsonld_organization(context):
    request = context["request"]
    site = context.get("site_settings")
    return {
        "payload": dumps_ld(organization_payload(request, site)),
        "csp_nonce": getattr(request, "csp_nonce", ""),
    }


@register.inclusion_tag("seo/partials/_jsonld_script.html", takes_context=True)
def jsonld_product(context, product, variant=None):
    request = context["request"]
    return {
        "payload": dumps_ld(product_payload(request, product, variant)),
        "csp_nonce": getattr(request, "csp_nonce", ""),
    }


@register.inclusion_tag("seo/partials/_jsonld_script.html", takes_context=True)
def jsonld_breadcrumbs(context, items):
    request = context["request"]
    pairs = []
    for item in items or []:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            pairs.append((item[0], item[1]))
        elif isinstance(item, dict):
            pairs.append((item["name"], item["url"]))
    return {
        "payload": dumps_ld(breadcrumbs_payload(request, pairs)),
        "csp_nonce": getattr(request, "csp_nonce", ""),
    }
