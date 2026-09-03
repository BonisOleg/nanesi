"""Форматування ціни/рейтингу для шаблонів вітрини (uk-UA стиль, без JS)."""
from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def uah(value):
    if value is None or value == "":
        return ""
    try:
        amount = Decimal(value)
    except (InvalidOperation, TypeError):
        return value
    amount = amount.to_integral_value() if amount == amount.to_integral_value() else round(amount, 2)
    text = f"{amount:,.0f}".replace(",", " ") if amount == int(amount) else f"{amount:,.2f}".replace(",", " ")
    return f"{text}\xa0грн"


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
