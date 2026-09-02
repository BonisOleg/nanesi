"""Залишено для шаблонів/імпортів; канон логіки — src.core.views_i18n."""
from src.core.views_i18n import localize_path, strip_language_prefix

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def language_neutral_path(context) -> str:
    request = context.get("request")
    if request is None:
        return "/"
    return strip_language_prefix(request.get_full_path())


@register.simple_tag(takes_context=True)
def language_url(context, lang: str) -> str:
    request = context.get("request")
    if request is None:
        return localize_path("/", lang)
    return localize_path(request.get_full_path(), lang)
