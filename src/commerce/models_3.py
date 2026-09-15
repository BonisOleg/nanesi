"""Черга подій замовлення для CRM/ERP (KeyCRM/SalesDrive) — «розетка в коді».

Доповнення §3: жива інтеграція поза обсягом Етапу 1, але checkout/place_order() вже
пише кожну значущу подію сюди (payload — незалежний від майбутніх змін Order снепшот),
щоб підʼєднати реальний адаптер пізніше без переробки ядра.
"""
from django.db import models

from src.core.models import TimeStampedModel


class OrderIntegrationEvent(TimeStampedModel):
    class EventType(models.TextChoices):
        ORDER_CREATED = "order_created", "Замовлення створено"
        STATUS_CHANGED = "status_changed", "Змінено статус"
        TTN_UPDATED = "ttn_updated", "Оновлено ТТН"

    class Status(models.TextChoices):
        PENDING = "pending", "Очікує відправки"
        SENT = "sent", "Відправлено"
        FAILED = "failed", "Помилка"

    order = models.ForeignKey(
        "commerce.Order", verbose_name="Замовлення", on_delete=models.CASCADE, related_name="integration_events",
    )
    event_type = models.CharField("Тип події", max_length=30, choices=EventType.choices)
    payload = models.JSONField("Дані (снепшот замовлення)", default=dict)
    status = models.CharField("Статус відправки", max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField("Помилка", blank=True)
    sent_at = models.DateTimeField("Відправлено", null=True, blank=True)

    class Meta:
        verbose_name = "Подія інтеграції (CRM)"
        verbose_name_plural = "Події інтеграції (CRM)"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.order} — {self.get_event_type_display()} ({self.get_status_display()})"
