"""Спільні абстрактні моделі (shared kernel), успадковуються всіма apps.

Не bounded context — лише щоб не копіювати created_at/updated_at та SEO-поля
в кожну модель окремо (ecommerce_db_schema_skill, крок 8).
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("Створено", auto_now_add=True)
    updated_at = models.DateTimeField("Оновлено", auto_now=True)

    class Meta:
        abstract = True


class SeoFieldsMixin(models.Model):
    """SEO override на сутності: title/description/keywords."""

    seo_title = models.CharField("SEO title", max_length=512, null=True, blank=True)
    seo_description = models.TextField("SEO description", null=True, blank=True)
    seo_keywords = models.CharField("SEO keywords", max_length=512, null=True, blank=True)

    class Meta:
        abstract = True


class SingletonModel(models.Model):
    """Абстрактна модель, що гарантує лише один запис у таблиці (pk=1)."""

    class Meta:
        abstract = True

    def clean(self) -> None:
        super().clean()
        if type(self).objects.exclude(pk=self.pk).exists():
            raise ValidationError(_("Дозволено лише один запис цього типу."))

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj
