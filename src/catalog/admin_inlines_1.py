"""Інлайни товару: варіанти, атрибути, фото, cross-sell, similar."""
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.utils.html import format_html
from unfold.admin import TabularInline

from .models import (
    ProductAttributeValue,
    ProductCrossSell,
    ProductImage,
    ProductSimilar,
    ProductVariant,
)


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


class ProductCrossSellInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        parent = self.instance
        for form in self.forms:
            cleaned = getattr(form, "cleaned_data", None) or {}
            if cleaned.get("DELETE"):
                continue
            to_product = cleaned.get("to_product")
            if to_product is not None and to_product == parent:
                form.add_error(
                    "to_product",
                    ValidationError(
                        "Супутній товар не може збігатися з поточним товаром.",
                    ),
                )


class ProductCrossSellInline(TabularInline):
    model = ProductCrossSell
    fk_name = "from_product"
    formset = ProductCrossSellInlineFormSet
    extra = 1
    autocomplete_fields = ["to_product"]
    fields = ("to_product", "position")
    verbose_name = "З цим купують"
    verbose_name_plural = "З цим купують"


class ProductSimilarInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        parent = self.instance
        for form in self.forms:
            cleaned = getattr(form, "cleaned_data", None) or {}
            if cleaned.get("DELETE"):
                continue
            to_product = cleaned.get("to_product")
            if to_product is not None and to_product == parent:
                form.add_error(
                    "to_product",
                    ValidationError(
                        "Схожий товар не може збігатися з поточним товаром.",
                    ),
                )


class ProductSimilarInline(TabularInline):
    model = ProductSimilar
    fk_name = "from_product"
    formset = ProductSimilarInlineFormSet
    extra = 1
    autocomplete_fields = ["to_product"]
    fields = ("to_product", "position")
    verbose_name = "Схожі товари"
    verbose_name_plural = "Схожі товари"
