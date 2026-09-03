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
    CATEGORY_POSTOMAT = "Postomat"
    CATEGORY_CARGO = "Cargo"

    ref = models.CharField("Ref (API)", max_length=64, unique=True)
    city = models.ForeignKey(NPCity, verbose_name="Місто", on_delete=models.CASCADE, related_name="warehouses")
    number = models.CharField("Номер відділення", max_length=16, blank=True)
    description = models.CharField("Опис / адреса", max_length=512)
    category = models.CharField("Категорія (API)", max_length=32, blank=True, db_index=True)
    is_active = models.BooleanField("Активне", default=True)

    class Meta:
        verbose_name = "Відділення / поштомат (НП)"
        verbose_name_plural = "Відділення / поштомати (НП)"
        ordering = ["city__name", "number"]

    @property
    def is_postomat(self) -> bool:
        return (self.category or "").lower() == self.CATEGORY_POSTOMAT.lower()

    @property
    def kind(self) -> str:
        return "postomat" if self.is_postomat else "warehouse"

    def display_name(self) -> str:
        from django.utils.translation import gettext as _

        if not self.is_postomat:
            return self.description
        low = self.description.lower()
        if "поштомат" in low or "почтомат" in low or "postomat" in low:
            return self.description
        return f"{_('Поштомат')} · {self.description}"

    def __str__(self) -> str:
        return self.display_name()
