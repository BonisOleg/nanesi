"""Форматування ціни/рейтингу для шаблонів вітрини (uk-UA стиль, без JS).

Вітрина: uk/ru → «грн», en → «UAH». API/аналітика лишають ISO UAH окремо.
"""
from decimal import Decimal, InvalidOperation

from django import template
from django.utils.translation import get_language

from src.catalog.selectors import localize_volume_label as _localize_volume_label

register = template.Library()


def currency_label(lang: str | None = None) -> str:
    code = (lang or get_language() or "uk").split("-")[0].lower()
    return "UAH" if code == "en" else "грн"


def format_money(value, *, lang: str | None = None) -> str:
    """«1 290 грн» / «1 290.50 UAH» — єдиний формат сум на вітрині."""
    if value is None or value == "":
        return ""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        return str(value)
    amount = amount.to_integral_value() if amount == amount.to_integral_value() else round(amount, 2)
    if amount == int(amount):
        text = f"{amount:,.0f}".replace(",", " ")
    else:
        text = f"{amount:,.2f}".replace(",", " ")
    return f"{text}\xa0{currency_label(lang)}"


@register.filter
def uah(value):
    return format_money(value)


@register.simple_tag
def currency_label_tag():
    return currency_label()


@register.filter
def localize_volume(value):
    return _localize_volume_label(value or "")


@register.filter
def stars(rating):
    if rating is None:
        return ""
    try:
        value = float(rating)
    except (TypeError, ValueError):
        return ""
    full = round(value)
    full = max(0, min(5, full))
    return "★" * full + "☆" * (5 - full)


@register.filter
def discount_percent(variant):
    if variant is None or variant.sale_price is None or not variant.retail_price:
        return None
    return round((1 - variant.sale_price / variant.retail_price) * 100)
