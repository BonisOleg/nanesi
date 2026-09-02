"""SiteSettings (singleton) + StaticPage + BlogPost + NewsletterLead.

Усі елементи, що змінюються в процесі роботи магазину (контакти, лого, безкоштовна
доставка, popup) — керовані з адмінки без участі розробника (Відповіді, «Додатково»).
"""
from decimal import Decimal

from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from src.core.models import SeoFieldsMixin, SingletonModel, TimeStampedModel

_hex_color_validator = RegexValidator(
    regex=r"^#[0-9A-Fa-f]{6}$",
    message="Формат кольору — HEX, напр. #C99B9B",
)


class SiteSettings(SingletonModel):
    site_name = models.CharField("Назва магазину", max_length=255, default="NANESI")
    tagline = models.CharField("Підпис під лого", max_length=255, blank=True, default="BEAUTY STORE")
    logo = models.ImageField("Логотип", upload_to="content/", null=True, blank=True)

    phone = models.CharField("Телефон", max_length=30, blank=True)
    email = models.EmailField("Email", blank=True)
    instagram_url = models.URLField("Instagram", blank=True)
    work_hours = models.CharField("Графік роботи", max_length=255, blank=True, default="Пн–Нд 10:00–20:00")
    address = models.CharField("Адреса / місто", max_length=255, blank=True, default="Київ, Україна")

    # Головна сторінка — банер (лист Nanesi: «з адмінки»)
    hero_title = models.CharField(
        "Заголовок банера", max_length=255, blank=True,
        default="Косметика для вашої природної краси",
    )
    hero_subtitle = models.TextField(
        "Підпис банера", blank=True,
        default="Мультибрендовий магазин догляду та макіяжу. Підібрані формули, "
        "прозорі склади та зручна доставка по Україні.",
    )
    hero_image = models.ImageField("Зображення банера", upload_to="content/", null=True, blank=True)
    topbar_promo_text = models.CharField(
        "Текст верхньої смужки", max_length=255, blank=True,
        default="Безкоштовна доставка від 1500 ₴",
    )

    # Безкоштовна доставка (лист Nanesi п.9) — сума керується тут, без розробника
    free_shipping_threshold = models.DecimalField(
        "Сума безкоштовної доставки, ₴",
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal("1500.00"),
        help_text=(
            "Поріг для прогрес-бару в кошику: «До безкоштовної доставки залишилось … грн». "
            "Порожнє поле — бар не показується. Текст верхньої смужки оновіть окремо."
        ),
    )

    # Мови (Доповнення §1): uk завжди активна; ru/en — тумблер
    ru_enabled = models.BooleanField("Російська мова увімкнена", default=True)
    en_enabled = models.BooleanField("Англійська мова увімкнена", default=True)

    # Кольори акценту (лист Nanesi, Доповнення §1) — зміна бренду без переробки вёрстки:
    # рендериться в /theme.css (CSS custom properties), base.css лише задає fallback-дефолт.
    accent_color = models.CharField(
        "Колір акценту", max_length=7, blank=True, validators=[_hex_color_validator],
        help_text="HEX, напр. #C99B9B. Порожнє — використовується дефолт з мокапу.",
    )
    accent_hover_color = models.CharField(
        "Колір акценту (hover)", max_length=7, blank=True, validators=[_hex_color_validator],
        help_text="HEX, напр. #A97878. Порожнє — використовується дефолт з мокапу.",
    )

    # Popup −10% за email (лист Nanesi п.10) — керування текстом/знижкою з адмінки
    promo_popup_enabled = models.BooleanField("Popup зі знижкою увімкнено", default=True)
    promo_popup_title = models.CharField("Заголовок popup", max_length=255, blank=True)
    promo_popup_text = models.TextField("Текст popup", blank=True)
    promo_popup_discount_percent = models.PositiveSmallIntegerField(
        "Знижка, %", default=10,
    )

    # Пікселі (Доповнення §1) — поля готові, підключення трекінгу — Етап E
    ga4_id = models.CharField("GA4 ID", max_length=50, blank=True)
    gtm_id = models.CharField("GTM ID", max_length=50, blank=True)
    meta_pixel_id = models.CharField("Meta Pixel ID", max_length=50, blank=True)
    tiktok_pixel_id = models.CharField("TikTok Pixel ID", max_length=50, blank=True)

    # Способи доставки/оплати — «вмикаються в адмінці» (лист Nanesi, карта v4.1)
    nova_poshta_enabled = models.BooleanField("Нова Пошта увімкнена", default=True)
    ukrposhta_enabled = models.BooleanField("Укрпошта увімкнена", default=True)
    card_payment_enabled = models.BooleanField(
        "Оплата карткою онлайн увімкнена", default=False,
        help_text="Автоматично недоступна на вітрині, поки не заповнені ключі LIQPAY_* у .env",
    )
    cash_on_delivery_enabled = models.BooleanField("Післяплата увімкнена", default=True)
    bank_transfer_enabled = models.BooleanField("Оплата за реквізитами увімкнена", default=True)
    bank_transfer_details = models.TextField(
        "Реквізити для оплати", blank=True,
        help_text="Показується клієнту при виборі «Оплата за реквізитами»",
    )

    # Сторінка «Дякуємо» після checkout — тексти з адмінки
    thank_you_title = models.CharField(
        "Дякуємо — заголовок",
        max_length=255,
        blank=True,
        default="Дякуємо за замовлення!",
    )
    thank_you_number_label = models.CharField(
        "Дякуємо — підпис до номера",
        max_length=255,
        blank=True,
        default="Номер замовлення",
        help_text="Перед номером, напр. «Номер замовлення». Сам номер підставляється автоматично.",
    )
    thank_you_body = models.TextField(
        "Дякуємо — текст під номером",
        blank=True,
        default=(
            "Ми зателефонуємо на {phone} для підтвердження. "
            "Статус можна відстежити, написавши нам номер замовлення."
        ),
        help_text=(
            "Можна змінювати слова навколо. Фрагмент {phone} не чіпайте і не перекладайте — "
            "на його місце підставиться телефон клієнта з замовлення. "
            "Якщо прибрати {phone}, телефон на сторінці не з’явиться."
        ),
    )

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self) -> str:
        return self.site_name

    def thank_you_title_display(self) -> str:
        return (self.thank_you_title or "").strip() or "Дякуємо за замовлення!"

    def thank_you_number_label_display(self) -> str:
        return (self.thank_you_number_label or "").strip() or "Номер замовлення"

    def thank_you_body_display(self, phone: str = "") -> str:
        tpl = (self.thank_you_body or "").strip() or (
            "Ми зателефонуємо на {phone} для підтвердження. "
            "Статус можна відстежити, написавши нам номер замовлення."
        )
        return tpl.replace("{phone}", phone or "")


class StaticPage(TimeStampedModel, SeoFieldsMixin):
    """Про нас / Доставка і оплата / Обмін та повернення / Оферта / Політика / Контакти."""

    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)
    body = models.TextField("Текст", blank=True)
    is_published = models.BooleanField("Опубліковано", default=True)

    class Meta:
        verbose_name = "Сторінка"
        verbose_name_plural = "Сторінки"
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("content:page_detail", kwargs={"slug": self.slug})


class BlogPost(TimeStampedModel, SeoFieldsMixin):
    title = models.CharField("Заголовок", max_length=255)
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)
    cover_image = models.ImageField("Обкладинка", upload_to="content/blog/", null=True, blank=True)
    body = models.TextField("Текст статті", blank=True)
    is_published = models.BooleanField("Опубліковано", default=False)
    published_at = models.DateTimeField("Дата публікації", null=True, blank=True)

    class Meta:
        verbose_name = "Стаття блогу"
        verbose_name_plural = "Блог"
        ordering = ["-published_at", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return reverse("content:blog_detail", kwargs={"slug": self.slug})


class NewsletterLead(TimeStampedModel):
    """Email з popup/інлайн-блоку підписки (лист Nanesi п.10) — джерело +
    згенерований одноразовий PromoCode для знижки за першу підписку."""

    class Source(models.TextChoices):
        POPUP = "popup", "Popup"
        INLINE = "inline", "Інлайн-блок на головній"

    email = models.EmailField("Email", unique=True)
    source = models.CharField("Джерело", max_length=20, choices=Source.choices, default=Source.POPUP)
    promo_code = models.ForeignKey(
        "commerce.PromoCode", verbose_name="Виданий промокод", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="newsletter_leads",
    )

    class Meta:
        verbose_name = "Email-лід (підписка)"
        verbose_name_plural = "Email-ліди (підписки)"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email


class TrustBadge(TimeStampedModel):
    """Блок «Переваги» на головній — тексти з адмінки; порожній список не показуємо."""

    icon_label = models.CharField(
        "Ключ іконки",
        max_length=32,
        blank=True,
        help_text="leaf / truck / award / refresh / headset — SVG у блоці переваг",
    )
    title = models.CharField("Заголовок", max_length=255)
    text = models.CharField("Текст", max_length=255, blank=True)
    is_active = models.BooleanField("Активний", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Перевага (головна)"
        verbose_name_plural = "Переваги (головна)"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return self.title
