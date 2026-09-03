from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TabbedTranslationAdmin
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action

from src.core.admin import TinyMCEAdminMixin

from . import translation  # noqa: F401 — реєстрація MT до TabbedTranslationAdmin.__init__
from .forms import SupplierImportForm
from .models import (
    Attribute,
    AttributeValue,
    Brand,
    Category,
    Collection,
    Product,
    ProductAttributeValue,
    ProductImage,
    ProductVariant,
    Review,
    ReviewImage,
    Supplier,
)


@admin.register(Category)
class CategoryAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    tinymce_fields = ("description",)
    list_display = ("name", "parent", "is_active", "show_in_header", "sort_order")
    list_editable = ("show_in_header", "sort_order")
    list_filter = ("is_active", "show_in_header", "parent")
    search_fields = ("name",)
    autocomplete_fields = ["parent"]
    prepopulated_fields = {"slug": ("name",)}
    list_display_links = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "slug", "parent", "description", "image")}),
        ("Вітрина", {"fields": ("is_active", "show_in_header", "sort_order")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )


@admin.register(Brand)
class BrandAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    tinymce_fields = ("description",)
    list_display = ("name", "get_logo_preview", "show_name", "is_active")
    list_filter = ("is_active", "show_name")
    list_editable = ("show_name",)
    search_fields = ("name",)
    readonly_fields = ("get_logo_preview",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        (None, {"fields": ("name", "slug", "logo", "get_logo_preview", "show_name", "description", "is_active")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )

    def get_logo_preview(self, obj: Brand):
        if obj.logo:
            return format_html('<img src="{}" style="height:32px">', obj.logo.url)
        return "—"

    get_logo_preview.short_description = "Логотип"


class ProductImageInline(TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "get_preview", "alt_text", "is_main", "sort_order")
    readonly_fields = ("get_preview",)

    def get_preview(self, obj: ProductImage):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:48px">', obj.image.url)
        return "—"

    get_preview.short_description = "Прев'ю"


class ProductVariantInline(TabularInline):
    model = ProductVariant
    extra = 1
    fields = (
        "sku", "barcode", "shade", "shade_hex", "shade_image", "volume",
        "cost_price", "retail_price", "sale_price",
        "stock_quantity", "is_active", "sort_order",
    )


class ProductAttributeValueInline(TabularInline):
    """attribute_values — M2M через through-модель, тому керується лише інлайном (admin.E013)."""

    model = ProductAttributeValue
    extra = 1
    autocomplete_fields = ["attribute_value"]


@admin.register(ProductVariant)
class ProductVariantAdmin(ModelAdmin):
    list_display = (
        "sku", "product", "shade", "volume",
        "cost_price", "retail_price", "sale_price", "stock_quantity", "is_active",
    )
    list_filter = ("is_active", "product__brand", "product__category")
    search_fields = ("sku", "barcode", "product__name")
    autocomplete_fields = ["product"]
    list_select_related = ("product", "product__brand")
    actions = ["apply_recommended_price"]

    @admin.action(description="Розрахувати рекомендовану ціну (за правилом націнки)")
    def apply_recommended_price(self, request, queryset):
        from src.pricing.services import PricingError, apply_markup_to_variant

        applied, failed = 0, 0
        for variant in queryset:
            try:
                apply_markup_to_variant(variant)
                applied += 1
            except PricingError as exc:
                failed += 1
                self.message_user(request, f"{variant.sku}: {exc}", level="warning")
        self.message_user(request, f"Ціну оновлено: {applied}, пропущено: {failed}")


@admin.register(Product)
class ProductAdmin(TinyMCEAdminMixin, TabbedTranslationAdmin, ModelAdmin):
    """modeltranslation вкладки uk/ru/en + TinyMCE на текстових описах (admin_skill)."""

    tinymce_fields = (
        "short_description",
        "description",
        "usage_instructions",
        "actives",
    )
    list_display = (
        "name", "brand", "category", "get_price_display",
        "get_stock_display", "is_active", "is_hit", "is_new",
    )
    list_filter = ("is_active", "is_hit", "is_new", "category", "brand", "supplier")
    search_fields = ("name", "variants__sku", "variants__barcode")
    autocomplete_fields = ["brand", "category", "supplier"]
    filter_horizontal = ("additional_categories",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductVariantInline, ProductAttributeValueInline, ProductImageInline]
    actions = ["apply_recommended_price_to_variants"]
    fieldsets = (
        (None, {"fields": ("name", "slug", "brand", "category", "additional_categories", "supplier")}),
        ("Опис", {"fields": ("short_description", "description", "usage_instructions", "actives", "inci")}),
        ("Статус", {"fields": ("is_active", "is_hit", "is_new")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "seo_keywords"), "classes": ("collapse",)}),
    )

    @admin.action(description="Розрахувати рекомендовану ціну (за правилом націнки)")
    def apply_recommended_price_to_variants(self, request, queryset):
        from src.pricing.services import PricingError, apply_markup_to_variant

        applied, failed = 0, 0
        variants = ProductVariant.objects.filter(product__in=queryset).select_related("product")
        for variant in variants:
            try:
                apply_markup_to_variant(variant)
                applied += 1
            except PricingError as exc:
                failed += 1
                self.message_user(request, f"{variant.sku}: {exc}", level="warning")
        self.message_user(request, f"Ціну оновлено: {applied}, пропущено: {failed}")

    def get_price_display(self, obj: Product):
        variant = obj.default_variant
        if not variant:
            return "—"
        if variant.sale_price is not None:
            return format_html(
                '<s>{}&nbsp;грн</s> <strong>{}&nbsp;грн</strong>',
                variant.retail_price,
                variant.sale_price,
            )
        return format_html('{}&nbsp;грн', variant.retail_price)

    get_price_display.short_description = "Ціна"

    def get_stock_display(self, obj: Product):
        variant = obj.default_variant
        if not variant:
            return "—"
        color = "green" if variant.in_stock else "red"
        label = f"{variant.stock_quantity} шт." if variant.in_stock else "Немає"
        return format_html('<span style="color:{}">{}</span>', color, label)

    get_stock_display.short_description = "Залишок"


@admin.register(Attribute)
class AttributeAdmin(ModelAdmin):
    list_display = ("name", "code", "is_filterable", "show_on_pdp", "sort_order")
    list_editable = ("is_filterable", "show_on_pdp", "sort_order")
    list_filter = ("is_filterable", "show_on_pdp")
    search_fields = ("name", "code")


@admin.register(AttributeValue)
class AttributeValueAdmin(TabbedTranslationAdmin, ModelAdmin):
    list_display = ("value", "attribute", "is_umbrella", "sort_order")
    list_editable = ("is_umbrella", "sort_order")
    list_filter = ("attribute", "is_umbrella")
    search_fields = ("value",)


@admin.register(Collection)
class CollectionAdmin(TabbedTranslationAdmin, ModelAdmin):
    list_display = ("name", "kind", "is_active", "sort_order", "get_image_preview")
    list_filter = ("kind", "is_active")
    filter_horizontal = ("products",)
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("get_image_preview",)
    fields = ("name", "slug", "kind", "image", "get_image_preview", "products", "is_active", "sort_order")

    def get_image_preview(self, obj: Collection):
        if obj.pk and obj.image:
            return format_html('<img src="{}" style="height:48px">', obj.image.url)
        return "—"

    get_image_preview.short_description = "Прев'ю"


class ReviewImageInline(TabularInline):
    model = ReviewImage
    extra = 0


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    """Модерація перед публікацією (Відповіді п.8) — is_approved за замовчуванням False."""

    list_display = ("product", "display_name", "rating", "is_verified_purchase", "is_approved", "created_at")
    list_filter = ("is_approved", "is_verified_purchase", "rating")
    search_fields = ("product__name", "author_name", "user__username", "text")
    autocomplete_fields = ["product", "user"]
    inlines = [ReviewImageInline]
    actions = ["approve_reviews"]

    @admin.action(description="Схвалити обрані відгуки")
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Схвалено відгуків: {updated}")


@admin.register(Supplier)
class SupplierAdmin(ModelAdmin):
    """Імпорт прайсу: Unfold-кнопка на картці постачальника і в рядку списку."""

    list_display = ("name", "contact_person", "phone", "is_active")
    search_fields = ("name",)
    actions_detail = ("import_price",)
    actions_row = ("import_price",)

    @action(
        description=_("Імпорт прайсу"),
        url_path="import",
        permissions=["change"],
    )
    def import_price(self, request, object_id):
        from django.contrib import messages
        from django.shortcuts import get_object_or_404, render

        from .services.imports import ImportError as SupplierImportError
        from .services.imports import import_supplier_file

        supplier = get_object_or_404(Supplier, pk=object_id)
        report = None

        if request.method == "POST":
            form = SupplierImportForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    report = import_supplier_file(
                        supplier=supplier,
                        uploaded_file=form.cleaned_data["file"],
                        name_locale=form.cleaned_data["name_locale"],
                    )
                    messages.success(
                        request,
                        f"Імпорт завершено: створено {report.created}, оновлено {report.updated}, "
                        f"пропущено {report.skipped}, помилок {len(report.errors)}.",
                    )
                except SupplierImportError as exc:
                    messages.error(request, str(exc))
        else:
            form = SupplierImportForm()

        context = {
            **self.admin_site.each_context(request),
            "title": f"Імпорт прайсу — {supplier.name}",
            "supplier": supplier,
            "form": form,
            "report": report,
            "opts": self.model._meta,
            "original": supplier,
            "has_view_permission": self.has_view_permission(request, supplier),
            "has_change_permission": self.has_change_permission(request, supplier),
            "has_add_permission": self.has_add_permission(request),
            "has_delete_permission": self.has_delete_permission(request, supplier),
        }
        return render(request, "admin/catalog/supplier/import.html", context)
