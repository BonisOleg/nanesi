"""modeltranslation: uk (основна) / ru / en — Доповнення §1 «Мови»."""
from modeltranslation.translator import TranslationOptions, translator

from .models import AttributeValue, Brand, Category, Collection, Product


class SeoTranslationMixin(TranslationOptions):
    fields = ("seo_title", "seo_description", "seo_keywords")


class CategoryTranslationOptions(SeoTranslationMixin):
    fields = ("name", "description") + SeoTranslationMixin.fields


class BrandTranslationOptions(SeoTranslationMixin):
    fields = ("name", "description") + SeoTranslationMixin.fields


class ProductTranslationOptions(SeoTranslationMixin):
    fields = (
        "name",
        "short_description",
        "description",
        "usage_instructions",
        "actives",
    ) + SeoTranslationMixin.fields


class CollectionTranslationOptions(TranslationOptions):
    fields = ("name",)


class AttributeValueTranslationOptions(TranslationOptions):
    fields = ("value",)


translator.register(Category, CategoryTranslationOptions)
translator.register(Brand, BrandTranslationOptions)
translator.register(Product, ProductTranslationOptions)
translator.register(Collection, CollectionTranslationOptions)
translator.register(AttributeValue, AttributeValueTranslationOptions)
