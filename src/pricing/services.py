"""Мутації ціноутворення — завжди явна дія (admin action), ніколи автоматично з синку.

SEC-09 (shop_security_skill): захист "продаж нижче собівартості" — тут шар 1
(guard у самому сервісі, що застосовує ціну). Шар 2 — CheckConstraint на
ProductVariant (catalog/models_1.py). Шар 3 — аудит-команда fix_prices_below_cost.
"""
from decimal import ROUND_HALF_UP, Decimal

from src.catalog.models import ProductVariant
from src.pricing.selectors import resolve_markup_percent


class PricingError(Exception):
    pass


def calculate_suggested_price(variant: ProductVariant) -> Decimal | None:
    """Рекомендована РРЦ = cost_price * (1 + markup% / 100). None, якщо немає
    ні закупівельної ціни, ні правила націнки — рахувати нема з чого."""
    if variant.cost_price is None:
        return None
    percent = resolve_markup_percent(variant)
    if percent is None:
        return None
    suggested = variant.cost_price * (Decimal("1") + percent / Decimal("100"))
    return suggested.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def apply_markup_to_variant(variant: ProductVariant) -> ProductVariant:
    """Явно застосувати рекомендовану ціну (admin action). SEC-09 guard: якщо
    результат нижче собівартості (напр. від'ємна/нульова націнка) — не пишемо."""
    suggested = calculate_suggested_price(variant)
    if suggested is None:
        raise PricingError(
            "Немає закупівельної ціни або правила націнки — рекомендовану ціну не розраховано",
        )
    if variant.cost_price is not None and suggested < variant.cost_price:
        raise PricingError("Розрахована ціна нижча за собівартість — перевірте правило націнки")
    variant.retail_price = suggested
    variant.save(update_fields=["retail_price", "updated_at"])
    return variant
