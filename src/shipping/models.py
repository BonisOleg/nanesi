"""Локальний денормалізований довідник НП (novaposhta_skill, Фаза 1).

Пошук на checkout — лише з цих таблиць (швидко, без rate limit), НЕ live-запитом
до API. Наповнюються командою np_sync_reference (Фаза 0.5: без ключа — порожні,
checkout падає назад на текстові поля Order.np_city_name/np_warehouse_name).
"""
from django.db import models


class NPCity(models.Model):
    ref = models.CharField("Ref (API)", max_length=64, unique=True)
    name = models.CharField("Назва", max_length=255, db_index=True)
    area = models.CharField("Область", max_length=255, blank=True)
    is_active = models.BooleanField("Активне", default=True)

    class Meta:
        verbose_name = "Місто (НП)"
        verbose_name_plural = "Міста (НП)"
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.area})" if self.area else self.name


class NPWarehouse(models.Model):
    ref = models.CharField("Ref (API)", max_length=64, unique=True)
    city = models.ForeignKey(NPCity, verbose_name="Місто", on_delete=models.CASCADE, related_name="warehouses")
    number = models.CharField("Номер відділення", max_length=16, blank=True)
    description = models.CharField("Опис / адреса", max_length=512)
    is_active = models.BooleanField("Активне", default=True)

    class Meta:
        verbose_name = "Відділення (НП)"
        verbose_name_plural = "Відділення (НП)"
        ordering = ["city__name", "number"]

    def __str__(self) -> str:
        return self.description
