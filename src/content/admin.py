from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import BlogPost, NewsletterLead, SiteSettings, StaticPage, TrustBadge


@admin.register(SiteSettings)
class SiteSettingsAdmin(ModelAdmin):
    """Singleton (admin_skill канон): get_or_create(pk=1), без add/delete.

    accent_color/accent_hover_color — звичайний текстовий HEX (не type="color"):
    натив-пікер завжди повертає значення (навіть #000000), тож поле ніколи не
    залишиться порожнім для fallback на дефолт із мокапу (/theme.css)."""

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
            "fields": ("promo_popup_enabled", "promo_popup_title", "promo_popup_text", "promo_popup_discount_percent"),
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


class TinyMCEAdminMixin:
    tinymce_fields: tuple[str, ...] = ("body",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tinymce_fields:
            kwargs["widget"] = TinyMCE()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(StaticPage)
class StaticPageAdmin(TinyMCEAdminMixin, ModelAdmin):
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
class BlogPostAdmin(TinyMCEAdminMixin, ModelAdmin):
    list_display = ("title", "get_cover_preview", "is_published", "published_at")
    list_filter = ("is_published",)
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("get_cover_preview",)
    fieldsets = (
        (None, {"fields": ("title", "slug", "cover_image", "get_cover_preview", "is_published", "published_at")}),
        ("Текст", {"fields": ("body",)}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )

    def get_cover_preview(self, obj: BlogPost):
        if obj.cover_image:
            return format_html('<img src="{}" style="height:48px">', obj.cover_image.url)
        return "—"

    get_cover_preview.short_description = "Обкладинка"


@admin.register(TrustBadge)
class TrustBadgeAdmin(ModelAdmin):
    list_display = ("title", "icon_label", "is_active", "sort_order")
    list_editable = ("sort_order",)
    list_filter = ("is_active",)


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
