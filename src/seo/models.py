"""SEO-посадкові (Лист Замовнику — карта v4.md, п. «SEO-посадкові»).

Конструктор в адмінці: довільна адреса, meta, текст, добірка товарів, index/noindex.
Конкретні сторінки й тексти клієнт заповнює сам пізніше — тут лише механізм.
"""
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from src.core.models import TimeStampedModel


class SeoLandingPage(TimeStampedModel):
    """Одна «фейкова» сторінка під SEO-запит: власний URL, meta, текст, товари."""

    title = models.CharField("Заголовок (H1)", max_length=255)
    path = models.SlugField(
        "Адреса (без слешів)", max_length=255, unique=True, allow_unicode=True,
        help_text="Частина URL після домену, напр. permanentnyj-makiyazh — сторінка відкриється на /permanentnyj-makiyazh/",
    )
    meta_title = models.CharField("SEO title", max_length=512, blank=True)
    meta_description = models.TextField("SEO description", blank=True)
    body = models.TextField(
        "Текст сторінки", blank=True,
        help_text="HTML дозволено (той самий редактор, що й для сторінок/блогу).",
    )
    products = models.ManyToManyField(
        "catalog.Product", verbose_name="Добірка товарів", blank=True, related_name="seo_landing_pages",
    )
    is_indexed = models.BooleanField(
        "Індексувати (index)", default=True,
        help_text="Вимкнено — сторінка отримує meta robots noindex,nofollow.",
    )
    is_active = models.BooleanField("Опубліковано", default=True)

    class Meta:
        verbose_name = "SEO-посадкова сторінка"
        verbose_name_plural = "SEO-посадкові сторінки"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.path:
            self.path = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        # Лендінги обслуговує catch-all content:page_detail (один сегмент URL).
        return reverse("content:page_detail", kwargs={"slug": self.path})
