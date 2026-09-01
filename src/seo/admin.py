from django.contrib import admin
from tinymce.widgets import TinyMCE
from unfold.admin import ModelAdmin

from .models import SeoLandingPage


@admin.register(SeoLandingPage)
class SeoLandingPageAdmin(ModelAdmin):
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

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "body":
            kwargs["widget"] = TinyMCE()
        return super().formfield_for_dbfield(db_field, request, **kwargs)
