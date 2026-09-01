"""Тільки читання — без мутацій (ecommerce_business_logic_skill, шар selectors)."""
from decimal import Decimal

from src.catalog.models import ProductVariant
from src.pricing.models import MarkupRule


def resolve_markup_percent(variant: ProductVariant) -> Decimal | None:
    """Найспецифічніше активне правило: product > brand > category > global."""
    product = variant.product

    rule = MarkupRule.objects.filter(
        scope=MarkupRule.Scope.PRODUCT, product=product, is_active=True,
    ).first()
    if rule:
        return rule.markup_percent

    rule = MarkupRule.objects.filter(
        scope=MarkupRule.Scope.BRAND, brand=product.brand, is_active=True,
    ).first()
    if rule:
        return rule.markup_percent

    rule = MarkupRule.objects.filter(
        scope=MarkupRule.Scope.CATEGORY, category=product.category, is_active=True,
    ).first()
    if rule:
        return rule.markup_percent

    rule = MarkupRule.objects.filter(scope=MarkupRule.Scope.GLOBAL, is_active=True).first()
    return rule.markup_percent if rule else None
