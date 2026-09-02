"""Cart/CartItem/PromoCode.

SEC-06 (shop_security_skill): CartItem тримає лише product_variant+qty, БЕЗ ціни.
Ціна рахується з БД при кожному рендері й при place_order() (SEC-02).
"""
from decimal import ROUND_HALF_UP, Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

from src.core.models import TimeStampedModel

_MONEY_QUANT = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """Округлення до копійок (2 знаки) — для виводу й збереження сум."""
    return (value or Decimal("0")).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)


class Cart(TimeStampedModel):
    """`updated_at` — база для майбутніх «покинутих кошиків» (Доповнення §3, не MVP)."""

    class Status(models.TextChoices):
        OPEN = "open", "Відкритий"
        CONVERTED = "converted", "Перетворений у замовлення"

    user = models.ForeignKey(
        "accounts.User", verbose_name="Користувач", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="carts",
    )
    session_key = models.CharField("Ключ сесії (гість)", max_length=40, blank=True, db_index=True)
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.OPEN)
    promo_code = models.ForeignKey(
        "commerce.PromoCode", verbose_name="Промокод", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="carts",
    )

    class Meta:
        verbose_name = "Кошик"
        verbose_name_plural = "Кошики"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        owner = self.user or self.session_key or "—"
        return f"Кошик #{self.pk} ({owner})"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, verbose_name="Кошик", on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(
        "catalog.ProductVariant", verbose_name="Варіант товару",
        on_delete=models.PROTECT, related_name="cart_items",
    )
    qty = models.PositiveIntegerField("Кількість", default=1, validators=[MinValueValidator(1)])
    added_at = models.DateTimeField("Додано", auto_now_add=True)

    class Meta:
        verbose_name = "Товар у кошику"
        verbose_name_plural = "Товари у кошику"
        constraints = [
            models.UniqueConstraint(fields=["cart", "product_variant"], name="uniq_cart_variant"),
        ]

    def __str__(self) -> str:
        return f"{self.product_variant} × {self.qty}"


class PromoCode(TimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Відсоток"
        FIXED = "fixed", "Фіксована сума"

    code = models.CharField("Код", max_length=50, unique=True)
    discount_type = models.CharField("Тип знижки", max_length=20, choices=DiscountType.choices)
    discount_value = models.DecimalField(
        "Розмір знижки", max_digits=10, decimal_places=2, validators=[MinValueValidator(0)],
    )
    valid_from = models.DateTimeField("Діє з", null=True, blank=True)
    valid_until = models.DateTimeField("Діє до", null=True, blank=True)
    max_uses = models.PositiveIntegerField("Максимум використань", null=True, blank=True, help_text="Порожнє — без обмеження")
    used_count = models.PositiveIntegerField("Використано разів", default=0)
    min_order_amount = models.DecimalField(
        "Мінімальна сума замовлення", max_digits=10, decimal_places=2, null=True, blank=True,
    )
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Промокод"
        verbose_name_plural = "Промокоди"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid_now(self, *, subtotal: Decimal | None = None) -> tuple[bool, str]:
        if not self.is_active:
            return False, _("Промокод неактивний")
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False, _("Промокод ще не почав діяти")
        if self.valid_until and now > self.valid_until:
            return False, _("Промокод вже не діє")
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False, _("Промокод вичерпано")
        if subtotal is not None and self.min_order_amount and subtotal < self.min_order_amount:
            return False, _("Мінімальна сума замовлення для промокоду — %(amount)s ₴") % {"amount": self.min_order_amount}
        return True, ""

    def calculate_discount(self, subtotal: Decimal) -> Decimal:
        if self.discount_type == self.DiscountType.PERCENT:
            discount = subtotal * self.discount_value / Decimal("100")
        else:
            discount = self.discount_value
        return money(min(discount, subtotal))
