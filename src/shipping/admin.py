from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import NPCity, NPWarehouse


@admin.register(NPCity)
class NPCityAdmin(ModelAdmin):
    """Довідникові дані (синк командою np_sync_reference) — у бічному меню не виводяться."""

    list_display = ("name", "area", "is_active")
    search_fields = ("name", "area")


@admin.register(NPWarehouse)
class NPWarehouseAdmin(ModelAdmin):
    list_display = ("description", "category", "city", "number", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("description", "number", "city__name")
    autocomplete_fields = ["city"]
