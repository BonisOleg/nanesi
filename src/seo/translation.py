from modeltranslation.translator import TranslationOptions, translator

from .models import SeoLandingPage


class SeoLandingPageTranslationOptions(TranslationOptions):
    fields = ("title", "meta_title", "meta_description", "body")


translator.register(SeoLandingPage, SeoLandingPageTranslationOptions)
