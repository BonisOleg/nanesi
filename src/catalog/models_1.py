"""Core-сутності каталогу: Category / Brand / Supplier / Product / ProductVariant / ProductImage.

Product = вітринна картка; ProductVariant = одиниця кошика/складу (відтінок/об'єм,
власний SKU/залишок/ціна) — лист Nanesi п.12: кушон №13/21/23 = 1 product + 3 variants.
"""
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from src.core.models import SeoFieldsMixin, TimeStampedModel

SHADE_HEX_RE = r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$"
SHADE_PREVIEW_LIMIT = 5


class Category(TimeStampedModel, SeoFieldsMixin):
    name = models.CharField("Назва", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)
    parent = models.ForeignKey(
        "self", verbose_name="Батьківська категорія", null=True, blank=True,
        on_delete=models.CASCADE, related_name="children",
    )
    description = models.TextField("Опис", blank=True)
    image = models.ImageField("Зображення", upload_to="catalog/categories/", null=True, blank=True)
    is_active = models.BooleanField("Активна", default=True)
    show_in_header = models.BooleanField(
        "Показувати в шапці",
        default=False,
        help_text="Нижня смуга навігації (3–4 корені). Повний список — у кнопці «Каталог».",
    )
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:category_detail", kwargs={"category_slug": self.slug})


class Brand(TimeStampedModel, SeoFieldsMixin):
    name = models.CharField("Назва", max_length=255, unique=True)
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)
    logo = models.ImageField("Логотип", upload_to="catalog/brands/", null=True, blank=True)
    show_name = models.BooleanField(
        "Показувати назву на вітрині",
        default=True,
        help_text="Зніми галочку, якщо логотип уже містить назву бренду (щоб не дублювати текст).",
    )
    description = models.TextField("Опис", blank=True)
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренди"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:brand_detail", kwargs={"brand_slug": self.slug})


class Supplier(TimeStampedModel):
    """Кожен товар прив'язаний до постачальника (Відповіді п.2). external_id/лог синку
    — заготовка під майбутній API/YML (Доповнення §1: архітектура під нових постачальників)."""

    name = models.CharField("Назва", max_length=255, unique=True)
    contact_person = models.CharField("Контактна особа", max_length=255, blank=True)
    phone = models.CharField("Телефон", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    notes = models.TextField("Примітки", blank=True)
    external_id = models.CharField(
        "Зовнішній ID (майбутній синк)", max_length=100, blank=True,
        help_text="Ідентифікатор постачальника у зовнішній системі — заготовка під API/YML",
    )
    is_active = models.BooleanField("Активний", default=True)

    class Meta:
        verbose_name = "Постачальник"
        verbose_name_plural = "Постачальники"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Product(TimeStampedModel, SeoFieldsMixin):
    """Вітринна картка товару. Ціна/залишок/SKU — на ProductVariant."""

    name = models.CharField("Назва", max_length=512)
    slug = models.SlugField("URL", max_length=512, unique=True, blank=True)
    brand = models.ForeignKey(
        Brand, verbose_name="Бренд", on_delete=models.PROTECT, related_name="products",
    )
    category = models.ForeignKey(
        Category, verbose_name="Основна категорія", on_delete=models.PROTECT,
        related_name="products",
    )
    additional_categories = models.ManyToManyField(
        Category, verbose_name="Додаткові категорії/напрями", blank=True,
        related_name="products_secondary",
        help_text="Наприклад: K-Beauty як напрям без обмеження основної категорії",
    )
    supplier = models.ForeignKey(
        Supplier, verbose_name="Постачальник", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="products",
    )
    # Країна виробництва, тип шкіри, проблема/призначення — через Attribute/AttributeValue
    # (attribute_values нижче), бо це фільтри з листа Nanesi п.7, і значення потребують
    # перекладу (uk/ru/en) так само, як і інші довідники.

    short_description = models.TextField("Короткий опис", blank=True)
    description = models.TextField("Опис", blank=True)
    usage_instructions = models.TextField("Спосіб застосування", blank=True)
    inci = models.TextField("Склад INCI", blank=True)
    actives = models.TextField("Активні компоненти", blank=True)

    attribute_values = models.ManyToManyField(
        "catalog.AttributeValue", verbose_name="Атрибути (фільтри)", blank=True,
        through="catalog.ProductAttributeValue", related_name="products",
    )

    is_active = models.BooleanField("Активний (видимий на сайті)", default=True)
    is_hit = models.BooleanField("Хіт продажів", default=False)
    is_new = models.BooleanField("Новинка", default=False)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)[:500]
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def default_variant(self) -> "ProductVariant | None":
        return self.variants.filter(is_active=True).order_by("sort_order", "pk").first()

    @property
    def storefront_variants(self) -> list["ProductVariant"]:
        """Активні SKU з prefetch (`variants.all()`), без зайвого SQL на картці."""
        variants = [item for item in self.variants.all() if item.is_active]
        variants.sort(key=lambda item: (item.sort_order, item.pk))
        return variants

    @property
    def shade_preview(self) -> dict:
        """Активні відтінки зі свотчем (hex або фото) — для карток каталогу."""
        items = [
            variant for variant in self.variants.all()
            if variant.is_active and variant.shade and variant.has_swatch
        ]
        extra = max(0, len(items) - SHADE_PREVIEW_LIMIT)
        return {"items": items[:SHADE_PREVIEW_LIMIT], "extra": extra}

    @property
    def is_on_sale(self) -> bool:
        variant = self.default_variant
        return bool(variant and variant.sale_price is not None)


class ProductVariant(TimeStampedModel):
    """Одиниця кошика/складу: власний SKU, залишок, ціна. shade/volume — з листа п.12."""

    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField("Артикул / SKU", max_length=100, unique=True)
    barcode = models.CharField("Штрихкод (EAN)", max_length=64, blank=True)

    shade = models.CharField("Відтінок", max_length=255, blank=True)
    shade_hex = models.CharField(
        "Колір відтінку (HEX)",
        max_length=7,
        blank=True,
        validators=[RegexValidator(SHADE_HEX_RE, "Формат #RGB або #RRGGBB")],
        help_text="Наприклад #E4C4A8. Якщо завантажене фото свотча — на вітрині показується фото.",
    )
    shade_image = models.ImageField(
        "Фото відтінку (свотч)",
        upload_to="catalog/shades/",
        blank=True,
        help_text="Для перламутру, глітеру, duo-chrome — коли HEX не передає колір.",
    )
    volume = models.CharField("Об'єм / варіант", max_length=100, blank=True)

    cost_price = models.DecimalField(
        "Закупівельна ціна", max_digits=10, decimal_places=2,
        null=True, blank=True, help_text="Лише в адмінці, на вітрині не показується",
    )
    retail_price = models.DecimalField(
        "Роздрібна ціна", max_digits=10, decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    sale_price = models.DecimalField(
        "Акційна ціна", max_digits=10, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text="Якщо заповнено — на вітрині показується стара ціна перекреслена",
    )

    stock_quantity = models.PositiveIntegerField("Залишок", default=0)
    is_active = models.BooleanField("Активний", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Варіант товару"
        verbose_name_plural = "Варіанти товару"
        ordering = ["sort_order", "pk"]
        constraints = [
            # SEC-09 (shop_security_skill), шар 2: не продавати нижче собівартості на рівні БД.
            models.CheckConstraint(
                check=models.Q(cost_price__isnull=True) | models.Q(retail_price__gte=models.F("cost_price")),
                name="productvariant_retail_gte_cost",
            ),
        ]

    def __str__(self) -> str:
        label = " / ".join(filter(None, [self.shade, self.volume]))
        return f"{self.product.name} ({label or self.sku})"

    def save(self, *args, **kwargs):
        hex_value = (self.shade_hex or "").strip().upper()
        if hex_value and not hex_value.startswith("#"):
            hex_value = f"#{hex_value}"
        self.shade_hex = hex_value
        super().save(*args, **kwargs)

    @property
    def option_label(self) -> str:
        return " / ".join(filter(None, [self.shade, self.volume])) or self.sku

    @property
    def has_swatch(self) -> bool:
        if self.shade_image:
            return True
        return bool(self.shade_hex)

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0

    @property
    def current_price(self):
        return self.sale_price if self.sale_price is not None else self.retail_price

    @property
    def discount_percent(self) -> int | None:
        if self.sale_price is None or self.retail_price <= 0:
            return None
        return round((1 - self.sale_price / self.retail_price) * 100)


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, verbose_name="Товар", on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("Зображення", upload_to="catalog/products/")
    alt_text = models.CharField("Alt-текст", max_length=255, blank=True)
    is_main = models.BooleanField("Головне фото", default=False)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Фото товару"
        verbose_name_plural = "Фото товару"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return f"Фото {self.product.name} #{self.sort_order}"
