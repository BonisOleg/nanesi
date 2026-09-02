from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from src.core.admin import TinyMCEAdminMixin

from . import translation  # noqa: F401 — MT registry до TabbedTranslationAdmin
from .models import BlogPost, NewsletterLead, SiteSettings, StaticPage, TrustBadge


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
        }),
        ("Кольори (акцент бренду)", {"fields": ("accent_color", "accent_hover_color")}),
        ("Доставка", {"fields": ("free_shipping_threshold",)}),
        ("Мови", {"fields": ("ru_enabled", "en_enabled")}),
        ("Popup зі знижкою", {
            "fields": (
                "promo_popup_enabled",
                "promo_popup_title",
                "promo_popup_text",
                "promo_popup_discount_percent",
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
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("get_cover_preview",)
    fieldsets = (
        (None, {
            "fields": (
                "title", "slug", "cover_image", "get_cover_preview",
                "is_published", "published_at",
            ),
        }),
        ("Текст", {"fields": ("body",)}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )

    def get_cover_preview(self, obj: BlogPost):
        if obj.cover_image:
            return format_html('<img src="{}" style="height:48px">', obj.cover_image.url)
        return "—"

    get_cover_preview.short_description = "Обкладинка"


@admin.register(TrustBadge)
class TrustBadgeAdmin(TabbedTranslationAdmin, ModelAdmin):
    list_display = ("title", "icon_label", "is_active", "sort_order")
    list_editable = ("icon_label", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "icon_label")


@admin.register(NewsletterLead)
class NewsletterLeadAdmin(ModelAdmin):
    """Лише перегляд/експорт лідів — створюються сайтом, не руками (popup/інлайн)."""

    list_display = ("email", "source", "promo_code", "created_at")
    list_filter = ("source",)
    search_fields = ("email",)
    readonly_fields = ("email", "source", "promo_code", "created_at", "updated_at")

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False
