"""Сателіти каталогу: Attribute/AttributeValue (фільтри), Collection, Review.

EAV-паттерн для фільтрів (тип шкіри, проблема, країна/напрям — лист Nanesi п.7),
щоб додавати нові фільтровані характеристики без нових колонок/міграцій.
"""
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from src.core.models import TimeStampedModel
from src.core.utils.images import validate_image


class Attribute(models.Model):
    code = models.SlugField("Код", max_length=100, unique=True)
    name = models.CharField("Назва", max_length=255)
    is_filterable = models.BooleanField("Показувати у фільтрах", default=True)
    show_on_pdp = models.BooleanField(
        "Показувати на картці товару",
        default=True,
        help_text="Зніми галочку, щоб атрибут лишався лише у фільтрах каталогу.",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Атрибут"
        verbose_name_plural = "Атрибути"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, verbose_name="Атрибут", on_delete=models.CASCADE, related_name="values")
    value = models.CharField("Значення", max_length=255)
    slug = models.SlugField("URL", max_length=255, blank=True)
    is_umbrella = models.BooleanField(
        "Покриває всі значення групи",
        default=False,
        help_text="Якщо товар має це значення (напр. «Усі типи»), інші значення тієї ж групи на картці ховаються.",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Значення атрибута"
        verbose_name_plural = "Значення атрибутів"
        ordering = ["sort_order", "value"]
        constraints = [
            models.UniqueConstraint(fields=["attribute", "value"], name="uniq_attribute_value"),
        ]

    def __str__(self) -> str:
        return f"{self.attribute.name}: {self.value}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.value, allow_unicode=True)[:255]
        super().save(*args, **kwargs)


class ProductAttributeValue(models.Model):
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE, related_name="product_attribute_values")
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE, related_name="product_links")

    class Meta:
        verbose_name = "Атрибут товару"
        verbose_name_plural = "Атрибути товару"
        constraints = [
            models.UniqueConstraint(fields=["product", "attribute_value"], name="uniq_product_attribute_value"),
        ]

    def __str__(self) -> str:
        return f"{self.product} — {self.attribute_value}"


class Collection(TimeStampedModel):
    """Хіти/новинки/акції/добірки — ручне або авто-керування підбіркою товарів."""

    class Kind(models.TextChoices):
        HIT = "hit", "Хіт продажів"
        NEW = "new", "Новинка"
        SALE = "sale", "Акція"
        CUSTOM = "custom", "Довільна підбірка"

    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)
    kind = models.CharField("Тип", max_length=20, choices=Kind.choices, default=Kind.CUSTOM)
    image = models.ImageField(
        "Зображення (промо на головній)",
        upload_to="catalog/collections/",
        null=True,
        blank=True,
        validators=[validate_image],
    )
    products = models.ManyToManyField("catalog.Product", verbose_name="Товари", blank=True, related_name="collections")
    is_active = models.BooleanField("Активна", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Підбірка"
        verbose_name_plural = "Підбірки"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:collection_detail", kwargs={"slug": self.slug})


class Review(TimeStampedModel):
    """Відгук з фото (Відповіді п.8, варіант Д): будь-хто, позначка «Підтверджена
    покупка» автоматично, якщо товар придбано на сайті. Модерація перед публікацією."""

    product = models.ForeignKey("catalog.Product", verbose_name="Товар", on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(
        "accounts.User", verbose_name="Користувач", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="reviews",
    )
    author_name = models.CharField("Ім'я автора", max_length=255, blank=True, help_text="Для відгуків без акаунту")
    rating = models.PositiveSmallIntegerField("Оцінка", validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField("Текст відгуку")
    is_verified_purchase = models.BooleanField("Підтверджена покупка", default=False)
    is_approved = models.BooleanField("Схвалено (опубліковано)", default=False)

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.product} — {self.rating}★"

    @property
    def display_name(self) -> str:
        if self.user_id:
            return self.user.get_full_name() or self.user.username
        return self.author_name or "Гість"


class ReviewImage(models.Model):
    review = models.ForeignKey(Review, verbose_name="Відгук", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(
        "Фото",
        upload_to="catalog/reviews/",
        validators=[validate_image],
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фото відгуку"
        verbose_name_plural = "Фото відгуків"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return f"Фото відгуку #{self.review_id}"
