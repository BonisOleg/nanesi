"""SiteSettings + готові URL перемикача мов на кожен request."""
from src.content.models import SiteSettings
from src.core.views_i18n import localize_path


def site_settings(request):
    path = request.get_full_path()
    return {
        "site_settings": SiteSettings.load(),
        # Готові цільові URL — шаблон не залежить від templatetag/reload.
        "lang_switch_urls": {
            "uk": localize_path(path, "uk"),
            "ru": localize_path(path, "ru"),
            "en": localize_path(path, "en"),
        },
    }
