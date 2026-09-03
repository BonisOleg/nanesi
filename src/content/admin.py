from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from src.core.admin import TinyMCEAdminMixin

from . import translation  # noqa: F401 — MT registry до TabbedTranslationAdmin
from .models import BlogPost, HeroBanner, NewsletterLead, SiteSettings, StaticPage, TrustBadge


@admin.register(SiteSettings)
class SiteSettingsAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    """Singleton (admin_skill): get_or_create(pk=1), без add/delete.

    accent_color/accent_hover_color — текстовий HEX (не type=color): натив-пікер
    завжди повертає значення, тож поле не лишиться порожнім для fallback /theme.css.
    """

    tinymce_fields = ("hero_subtitle", "promo_popup_text", "bank_transfer_details")
    fieldsets = (
        ("Бренд", {"fields": ("site_name", "tagline", "logo")}),
        ("Контакти", {"fields": ("phone", "email", "instagram_url", "work_hours", "address")}),
        ("Головна — банер і смужка", {
            "fields": ("topbar_promo_text", "hero_title", "hero_subtitle", "hero_image"),
            "description": (
                "Fallback, якщо немає активних записів у «Банери головної». "
                "Seed також підставляє ці поля в перший слайд."
            ),
        }),
        ("Кольори (акцент бренду)", {"fields": ("accent_color", "accent_hover_color")}),
        ("Доставка", {
            "fields": ("free_shipping_threshold",),
            "description": (
                "Сума для прогрес-бару в кошику. Змінюється тут — без участі розробника. "
                "Текст верхньої смужки («Безкоштовна доставка від …») оновіть у блоці вище."
            ),
        }),
        ("Мови", {"fields": ("ru_enabled", "en_enabled")}),
        ("Popup зі знижкою", {
            "fields": (
                "promo_popup_enabled",
                "promo_popup_title",
                "promo_popup_text",
                "promo_popup_discount_percent",
            ),
        }),
        ("Сторінка «Дякуємо»", {
            "fields": (
                "thank_you_title", "thank_you_number_label", "thank_you_body",
                "payment_pending_title", "payment_pending_body",
            ),
            "description": (
                "Тексти після оформлення замовлення. "
                "У полі «текст під номером» залишайте {phone} як є (латиницею в фігурних дужках) — "
                "це автоматично заміниться на телефон покупця. Решту речення можна редагувати. "
                "Блок «Оплата не пройшла» — лише для неоплаченої картки: заголовок і текст "
                "з рекомендацією спробувати ще або обрати інший спосіб."
            ),
        }),
        ("Доставка і оплата", {
            "fields": (
                "nova_poshta_enabled", "ukrposhta_enabled",
                "card_payment_enabled", "cash_on_delivery_enabled",
                "bank_transfer_enabled", "bank_transfer_details",
            ),
        }),
        ("Пікселі (GTM/GA4/Meta/TikTok)", {
            "fields": ("ga4_id", "gtm_id", "meta_pixel_id", "tiktok_pixel_id"),
            "classes": ("collapse",),
        }),
    )

    def has_add_permission(self, request) -> bool:
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _created = SiteSettings.objects.get_or_create(pk=1)
        return HttpResponseRedirect(reverse("admin:content_sitesettings_change", args=[obj.pk]))


@admin.register(StaticPage)
class StaticPageAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    tinymce_fields = ("body",)
    list_display = ("title", "slug", "is_published", "updated_at")
    list_filter = ("is_published",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "slug", "is_published")}),
        ("Текст", {"fields": ("body",)}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )


@admin.register(BlogPost)
class BlogPostAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    tinymce_fields = ("body",)
    list_display = ("title", "get_cover_preview", "is_published", "published_at")
    list_filter = ("is_published",)
    search_fields = ("title", "h1")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ["products"]
    readonly_fields = ("get_cover_preview",)
    fieldsets = (
        (None, {
            "fields": (
                "title", "h1", "slug", "cover_image", "get_cover_preview",
                "is_published", "published_at",
            ),
        }),
        ("Текст", {"fields": ("body",)}),
        ("Добірка товарів", {"fields": ("products",)}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )

    def get_cover_preview(self, obj: BlogPost):
        if obj.cover_image:
            return format_html('<img src="{}" style="height:48px">', obj.cover_image.url)
        return "—"

    get_cover_preview.short_description = "Обкладинка"


@admin.register(HeroBanner)
class HeroBannerAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    tinymce_fields = ("subtitle",)
    list_display = (
        "title", "get_image_preview", "get_bg_preview",
        "overlay_blur", "is_active", "sort_order",
    )
    list_editable = ("is_active", "sort_order", "overlay_blur")
    list_filter = ("is_active",)
    search_fields = ("title", "eyebrow", "button_text")
    readonly_fields = ("get_image_preview", "get_bg_preview")
    ordering = ("sort_order", "pk")
    fieldsets = (
        (None, {
            "fields": (
                "eyebrow", "title", "subtitle",
                "button_text", "button_url",
                "is_active", "sort_order",
            ),
        }),
        ("Зображення справа", {
            "fields": ("image", "get_image_preview"),
        }),
        ("Фон слайда", {
            "fields": (
                "background_image", "get_bg_preview",
                "overlay_color", "overlay_opacity", "overlay_blur",
            ),
            "description": (
                "Шари ззаду вперед: 1) фото фону → 2) блюр фото → 3) кольорова підложка. "
                "При прозорості 0% підложка невидима — зміна кольору не вплине на вітрину. "
                "Щоб побачити колір, поставте прозорість 40–80%. "
                "Блюр 0 = чітке фото; кожен слайд має свої значення (дивіться саме той, який редагуєте)."
            ),
        }),
    )

    def get_image_preview(self, obj: HeroBanner):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:64px;border-radius:6px">', obj.image.url)
        return "—"

    get_image_preview.short_description = "Прев’ю справа"

    def get_bg_preview(self, obj: HeroBanner):
        if obj.pk and obj.background_image:
            return format_html(
                '<img src="{}" style="height:64px;border-radius:6px;object-fit:cover;width:96px">',
                obj.background_image.url,
            )
        return "—"

    get_bg_preview.short_description = "Прев’ю фону"


@admin.register(TrustBadge)
class TrustBadgeAdmin(TabbedTranslationAdmin, ModelAdmin):
    list_display = ("title", "icon_label", "is_active", "sort_order")
    list_editable = ("icon_label", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "icon_label")


@admin.register(NewsletterLead)
class NewsletterLeadAdmin(ModelAdmin):
    """Лише перегляд лідів — створюються сайтом, не руками (popup/інлайн)."""

    list_display = ("email", "source", "promo_code", "created_at")
    list_filter = ("source",)
    search_fields = ("email",)
    readonly_fields = ("email", "source", "promo_code", "created_at", "updated_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        # False → Django ховає модель (has_view = has_change за замовчуванням).
        return False

    def has_view_permission(self, request, obj=None) -> bool:
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None) -> bool:
        return request.user.is_superuser
