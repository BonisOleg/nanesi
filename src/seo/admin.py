from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin

from src.core.admin import TinyMCEAdminMixin

from . import translation  # noqa: F401 — MT registry до TabbedTranslationAdmin
from .models import SeoLandingPage


@admin.register(SeoLandingPage)
class SeoLandingPageAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    tinymce_fields = ("body",)
    list_display = ("title", "path", "is_active", "is_indexed", "updated_at")
    list_filter = ("is_active", "is_indexed")
    search_fields = ("title", "path")
    autocomplete_fields = ["products"]
    prepopulated_fields = {"path": ("title",)}
    fieldsets = (
        (None, {"fields": ("title", "path", "is_active", "is_indexed")}),
        ("Meta", {"fields": ("meta_title", "meta_description")}),
        ("Текст", {"fields": ("body",)}),
        ("Добірка товарів", {"fields": ("products",)}),
    )
