from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import MarkupRule


@admin.register(MarkupRule)
class MarkupRuleAdmin(ModelAdmin):
    list_display = ("scope", "category", "brand", "product", "markup_percent", "is_active")
    list_filter = ("scope", "is_active")
    autocomplete_fields = ["category", "brand", "product"]
    fieldsets = (
        (None, {"fields": ("scope", "markup_percent", "is_active")}),
        ("Ціль правила (заповнити лише поле, що відповідає рівню)", {
            "fields": ("category", "brand", "product"),
        }),
    )
