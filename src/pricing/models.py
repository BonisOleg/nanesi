"""Правило націнки: product > brand > category > global (найспецифічніше виграє).

Інваріант (Доповнення §1): роздрібна ціна НІКОЛИ не пишеться автоматично з фіду
постачальника. MarkupRule лише РАХУЄ рекомендовану ціну з cost_price — застосування
завжди явна дія адміністратора (admin action), не сигнал/post_save.
"""
from django.core.validators import MinValueValidator
from django.db import models

from src.core.models import TimeStampedModel


class MarkupRule(TimeStampedModel):
    class Scope(models.TextChoices):
        GLOBAL = "global", "Глобально (за замовчуванням)"
        CATEGORY = "category", "Категорія"
        BRAND = "brand", "Бренд"
        PRODUCT = "product", "Товар"

    scope = models.CharField("Рівень", max_length=20, choices=Scope.choices)
    category = models.ForeignKey(
        "catalog.Category", verbose_name="Категорія", null=True, blank=True,
        on_delete=models.CASCADE, related_name="markup_rules",
    )
    brand = models.ForeignKey(
        "catalog.Brand", verbose_name="Бренд", null=True, blank=True,
        on_delete=models.CASCADE, related_name="markup_rules",
    )
    product = models.ForeignKey(
        "catalog.Product", verbose_name="Товар", null=True, blank=True,
        on_delete=models.CASCADE, related_name="markup_rules",
    )
    markup_percent = models.DecimalField(
        "Націнка, %", max_digits=6, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    is_active = models.BooleanField("Активне", default=True)

    class Meta:
        verbose_name = "Правило націнки"
        verbose_name_plural = "Правила націнки"
        ordering = ["scope"]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(scope="global", category__isnull=True, brand__isnull=True, product__isnull=True)
                    | models.Q(scope="category", category__isnull=False, brand__isnull=True, product__isnull=True)
                    | models.Q(scope="brand", category__isnull=True, brand__isnull=False, product__isnull=True)
                    | models.Q(scope="product", category__isnull=True, brand__isnull=True, product__isnull=False)
                ),
                name="markuprule_scope_target_matches",
            ),
        ]

    def __str__(self) -> str:
        target = self.product or self.brand or self.category or "Глобально"
        return f"{target} — {self.markup_percent}%"
