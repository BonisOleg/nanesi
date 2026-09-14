"""Order/OrderItem/OrderStatusLog.

Snapshot-паттерн (ERR-SCHEMA-04 з novaposhta_skill): ціна/назва/SKU фіксуються на
OrderItem у момент замовлення й НЕ залежать від подальших змін Product/ProductVariant.
Доставка (np_city_name тощо) — теж снепшот, не FK на мутабельний довідник.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from src.commerce.models_1 import PromoCode
from src.core.models import TimeStampedModel


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = "new", _("Нове")
        CONFIRMED = "confirmed", _("Підтверджено")
        PAID = "paid", _("Оплачено")
        ASSEMBLING = "assembling", _("Збирається")
        SHIPPED = "shipped", _("Відправлено")
        DELIVERED = "delivered", _("Доставлено")
        CANCELLED = "cancelled", _("Скасовано")

    class DeliveryMethod(models.TextChoices):
        NOVA_POSHTA_WAREHOUSE = "np_warehouse", _("Нова Пошта")
        UKRPOSHTA = "ukrposhta", _("Укрпошта")

    class PaymentMethod(models.TextChoices):
        CARD_ONLINE = "card_online", _("Оплата карткою онлайн")
        CASH_ON_DELIVERY = "cod", _("Післяплата")
        BANK_TRANSFER = "bank_transfer", _("За реквізитами")

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", _("Не оплачено")
        PAID = "paid", _("Оплачено")
        REFUNDED = "refunded", _("Повернено")

    number = models.CharField("Номер замовлення", max_length=32, unique=True, blank=True)
    user = models.ForeignKey(
        "accounts.User", verbose_name="Користувач", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders",
    )
    status = models.CharField("Статус", max_length=20, choices=Status.choices, default=Status.NEW)
    stock_restored = models.BooleanField(
        "Залишок повернуто на склад",
        default=False,
        help_text="True після скасування — щоб не повернути qty двічі",
    )

    # Контакт (гість-checkout, Відповіді п.6): телефон та/або email
    full_name = models.CharField("ПІБ", max_length=255)
    phone = models.CharField("Телефон", max_length=20)
    email = models.EmailField("Email", blank=True)

    # Доставка — снепшот (не FK на мутабельний довідник НП)
    delivery_method = models.CharField("Спосіб доставки", max_length=20, choices=DeliveryMethod.choices)
    np_city_name = models.CharField("Місто (НП)", max_length=255, blank=True)
    np_city_ref = models.CharField("Ref міста (НП)", max_length=64, blank=True)
    np_warehouse_name = models.CharField("Відділення / поштомат (НП)", max_length=255, blank=True)
    np_warehouse_ref = models.CharField("Ref відділення / поштомату (НП)", max_length=64, blank=True)
    ukrposhta_index = models.CharField("Індекс (Укрпошта)", max_length=5, blank=True)
    ukrposhta_address = models.CharField("Адреса (Укрпошта)", max_length=512, blank=True)

    # Оплата
    payment_method = models.CharField("Спосіб оплати", max_length=20, choices=PaymentMethod.choices)
    payment_status = models.CharField("Статус оплати", max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    payment_intent_id = models.CharField("ID транзакції платіжки", max_length=100, blank=True)
    payment_idempotency_key = models.CharField(
        "Idempotency-ключ webhook", max_length=100, blank=True, null=True, unique=True,
    )
    paid_at = models.DateTimeField("Дата оплати", null=True, blank=True)

    # Суми
    subtotal = models.DecimalField("Сума товарів", max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField("Знижка", max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField("Вартість доставки", max_digits=10, decimal_places=2, null=True, blank=True)
    total = models.DecimalField("Разом", max_digits=10, decimal_places=2, default=0)

    promo_code = models.ForeignKey(
        PromoCode, verbose_name="Промокод", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders",
    )
    promo_code_snapshot = models.CharField("Промокод (текст)", max_length=50, blank=True)

    comment = models.TextField("Коментар клієнта", blank=True)

    # Логістика — діагностика (novaposhta_skill, Фаза 4.3)
    ttn_number = models.CharField("ТТН", max_length=32, blank=True)
    shipping_error = models.TextField("Помилка доставки (API)", blank=True)

    # SalesDrive — id заявки після успішного create через outbox
    salesdrive_order_id = models.PositiveIntegerField(
        "ID заявки SalesDrive", null=True, blank=True, db_index=True,
    )

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.number or f"Замовлення #{self.pk}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.number:
            self.number = f"NS-{self.pk:06d}"
            super().save(update_fields=["number"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name="Замовлення", on_delete=models.CASCADE, related_name="items")
    product_variant = models.ForeignKey(
        "catalog.ProductVariant", verbose_name="Варіант товару", null=True,
        on_delete=models.SET_NULL, related_name="order_items",
    )
    product_name = models.CharField("Назва товару (знімок)", max_length=512)
    sku = models.CharField("SKU (знімок)", max_length=100)
    unit_price = models.DecimalField("Ціна за одиницю (знімок)", max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField("Кількість")
    line_total = models.DecimalField("Сума рядка", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "Товар замовлення"
        verbose_name_plural = "Товари замовлення"

    def __str__(self) -> str:
        return f"{self.product_name} × {self.qty}"


class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, verbose_name="Замовлення", on_delete=models.CASCADE, related_name="status_logs")
    from_status = models.CharField("Було", max_length=20, blank=True)
    to_status = models.CharField("Стало", max_length=20)
    note = models.TextField("Примітка", blank=True)
    changed_by = models.ForeignKey(
        "accounts.User", verbose_name="Змінив", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )
    created_at = models.DateTimeField("Дата", auto_now_add=True)

    class Meta:
        verbose_name = "Історія статусу замовлення"
        verbose_name_plural = "Історія статусів замовлень"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.order} — {self.from_status} → {self.to_status}"
