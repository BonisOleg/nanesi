from modeltranslation.translator import TranslationOptions, translator

from .models import BlogPost, HeroBanner, SiteSettings, StaticPage, TrustBadge


class SeoTranslationMixin(TranslationOptions):
    fields = ("seo_title", "seo_description", "seo_keywords")


class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "site_name", "tagline", "promo_popup_title", "promo_popup_text",
        "hero_title", "hero_subtitle", "topbar_promo_text", "work_hours", "address",
        "bank_transfer_details",
        "thank_you_title", "thank_you_number_label", "thank_you_body",
        "payment_pending_title", "payment_pending_body",
    )


class StaticPageTranslationOptions(SeoTranslationMixin):
    fields = ("title", "body") + SeoTranslationMixin.fields


class BlogPostTranslationOptions(SeoTranslationMixin):
    fields = ("title", "h1", "body") + SeoTranslationMixin.fields


class TrustBadgeTranslationOptions(TranslationOptions):
    fields = ("title", "text")


class HeroBannerTranslationOptions(TranslationOptions):
    fields = ("eyebrow", "title", "subtitle", "button_text")


translator.register(SiteSettings, SiteSettingsTranslationOptions)
translator.register(StaticPage, StaticPageTranslationOptions)
translator.register(BlogPost, BlogPostTranslationOptions)
translator.register(TrustBadge, TrustBadgeTranslationOptions)
translator.register(HeroBanner, HeroBannerTranslationOptions)
