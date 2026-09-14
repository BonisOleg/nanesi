"""SiteSettings (singleton) + HeroBanner + StaticPage + BlogPost + NewsletterLead.

Усі елементи, що змінюються в процесі роботи магазину (контакти, лого, безкоштовна
доставка, popup, банери головної) — керовані з адмінки без участі розробника.
"""
from decimal import Decimal
import re

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
        default="Безкоштовна доставка від 1500\xa0грн",
    )

    # Безкоштовна доставка (лист Nanesi п.9) — сума, тумблер і методи з адмінки
    free_shipping_enabled = models.BooleanField(
        "Безкоштовна доставка увімкнена",
        default=True,
        help_text="Вимкніть, щоб сховати прогрес-бар і не застосовувати нульову доставку.",
    )
    free_shipping_threshold = models.DecimalField(
        "Сума безкоштовної доставки, грн",
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
    free_shipping_np = models.BooleanField(
        "Діє для Нової Пошти",
        default=True,
    )
    free_shipping_ukrposhta = models.BooleanField(
        "Діє для Укрпошти",
        default=True,
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
    payment_pending_title = models.CharField(
        "Оплата не пройшла — заголовок",
        max_length=255,
        blank=True,
        default="Оплата не пройшла",
        help_text="Показується на «Дякуємо», якщо карткова оплата неуспішна / ще не оплачено.",
    )
    payment_pending_body = models.TextField(
        "Оплата не пройшла — текст",
        blank=True,
        default=(
            "Спробуйте оплатити ще раз або оберіть інший спосіб оплати нижче. "
            "Замовлення вже створено і чекає на оплату."
        ),
        help_text="Рекомендація клієнту після помилки оплати карткою. Редагується тут.",
    )

    class Meta:
        verbose_name = "Налаштування сайту"
        verbose_name_plural = "Налаштування сайту"

    def __str__(self) -> str:
        return self.site_name

    def free_shipping_is_configured(self) -> bool:
        """Тумблер + поріг + хоча б один спосіб доставки."""
        return (
            self.free_shipping_enabled
            and bool(self.free_shipping_threshold and self.free_shipping_threshold > 0)
            and (self.free_shipping_np or self.free_shipping_ukrposhta)
        )

    def free_shipping_covers(self, delivery_method: str) -> bool:
        if not self.free_shipping_is_configured():
            return False
        if delivery_method == "np_warehouse":
            return self.free_shipping_np
        if delivery_method == "ukrposhta":
            return self.free_shipping_ukrposhta
        return False

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

    def payment_pending_title_display(self) -> str:
        return (self.payment_pending_title or "").strip() or "Оплата не пройшла"

    def payment_pending_body_display(self) -> str:
        return (self.payment_pending_body or "").strip() or (
            "Спробуйте оплатити ще раз або оберіть інший спосіб оплати нижче. "
            "Замовлення вже створено і чекає на оплату."
        )

    def bank_requisites_for_display(self) -> dict:
        """HTML + plain text для блоку реквізитів (Дякуємо / Доставка і оплата)."""
        from django.utils.html import strip_tags

        html = (self.bank_transfer_details or "").strip()
        if not self.bank_transfer_enabled or not html:
            return {}
        plain = strip_tags(html).replace("\xa0", " ").strip()
        return {
            "bank_requisites_html": html,
            "bank_requisites_plain": plain,
        }


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
    h1 = models.CharField(
        "H1",
        max_length=255,
        blank=True,
        help_text="Якщо порожнє — на сторінці показується Заголовок.",
    )
    slug = models.SlugField("URL", max_length=255, unique=True, blank=True)
    cover_image = models.ImageField("Обкладинка", upload_to="content/blog/", null=True, blank=True)
    body = models.TextField("Текст статті", blank=True)
    products = models.ManyToManyField(
        "catalog.Product",
        verbose_name="Добірка товарів",
        blank=True,
        related_name="blog_posts",
    )
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

    @property
    def display_h1(self) -> str:
        return (self.h1 or "").strip() or self.title


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


class HeroBanner(TimeStampedModel):
    """Слайд hero-банера на головній. Порожній список → fallback на SiteSettings.hero_*."""

    eyebrow = models.CharField("Рядок над заголовком", max_length=255, blank=True)
    title = models.CharField("Заголовок", max_length=255)
    subtitle = models.TextField("Підзаголовок", blank=True)
    button_text = models.CharField(
        "Текст кнопки", max_length=80, blank=True, default="До каталогу",
    )
    button_url = models.CharField(
        "Посилання кнопки",
        max_length=512,
        blank=True,
        default="/katalog/",
        help_text="Відносний шлях або повний URL, напр. /katalog/ чи /dobirka/aktsii/",
    )
    image = models.ImageField(
        "Зображення справа", upload_to="content/hero/", null=True, blank=True,
    )
    background_image = models.ImageField(
        "Фонове зображення",
        upload_to="content/hero/bg/",
        null=True,
        blank=True,
        help_text="На весь слайд (desktop і mobile). Порожнє — бежевий фон.",
    )
    overlay_color = models.CharField(
        "Колір підложки",
        max_length=7,
        blank=True,
        default="#EFE9E1",
        validators=[_hex_color_validator],
        help_text=(
            "HEX, напр. #EFE9E1. Видно лише коли «Прозорість підложки» > 0. "
            "При 0% колір повністю прозорий — зміна HEX нічого не змінить на вітрині."
        ),
    )
    overlay_opacity = models.PositiveSmallIntegerField(
        "Прозорість підложки, %",
        default=72,
        help_text=(
            "Наскільки щільно колір накриває фото: "
            "0 = фото без підложки (колір не видно), "
            "50 = легка вуаль, "
            "100 = суцільний колір без фото. "
            "Щоб побачити зміну кольору — поставте 40–80."
        ),
    )
    overlay_blur = models.PositiveSmallIntegerField(
        "Блюр фону, px",
        default=10,
        help_text=(
            "Розмиття саме фото фону (не підложки): "
            "0 = чітке фото, 6–12 = легкий блюр, до 40. "
            "Порівнюйте на одному слайді (автопрокрутка перемикає слайди з різними значеннями)."
        ),
    )
    is_active = models.BooleanField("Активний", default=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Банер головної"
        verbose_name_plural = "Банери головної"
        ordering = ["sort_order", "pk"]

    def __str__(self) -> str:
        return self.title or f"Банер #{self.pk}"

    @property
    def overlay_opacity_css(self) -> str:
        value = max(0, min(100, int(self.overlay_opacity or 0)))
        return f"{value / 100:.2f}"

    @property
    def overlay_blur_css(self) -> str:
        value = max(0, min(40, int(self.overlay_blur or 0)))
        return f"{value}px"

    @property
    def overlay_rgba(self) -> str:
        """Колір підложки з альфою — один CSS-шар (видно лише при opacity > 0)."""
        raw = (self.overlay_color or "#EFE9E1").strip()
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", raw):
            raw = "#EFE9E1"
        r = int(raw[1:3], 16)
        g = int(raw[3:5], 16)
        b = int(raw[5:7], 16)
        a = max(0, min(100, int(self.overlay_opacity or 0))) / 100
        return f"rgba({r}, {g}, {b}, {a:.2f})"


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
