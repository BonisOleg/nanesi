"""SiteSettings — на кожній сторінці (лого, контакти, банер, перемикач мов)."""
from src.content.models import SiteSettings


def site_settings(request):
    return {"site_settings": SiteSettings.load()}
