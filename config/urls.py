from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from django.urls import include, path

from src.content.views import theme_css
from src.core.views_i18n import set_language
from src.seo.sitemaps import sitemaps
from src.seo.views import robots_txt


def healthz(_request):
    return HttpResponse("ok")


# Без префікса мови (uk без /uk/) — здоров'я, адмінка, AJAX-довідники НП, медіа/статика,
# перемикач мов і технічні файли для пошукових ботів.
urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path(settings.ADMIN_URL, admin.site.urls),
    path("shipping/", include("src.shipping.urls")),
    # Власний set_language — захист від /ru/ru (стандартний Django translate_url ламається).
    path("i18n/setlang/", set_language, name="set_language"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("theme.css", theme_css, name="theme_css"),
]

# i18n_patterns: uk — без префікса (Відповіді, карта v4.1: «на одній схемі»), ru/en — з /ru/, /en/.
urlpatterns += i18n_patterns(
    path("", include("src.catalog.urls")),
    path("", include("src.commerce.urls")),
    path("", include("src.accounts.urls")),
    # content.urls містить catch-all <str:slug>/ (статичні сторінки + SEO-лендінги) — має йти ОСТАННІМ.
    path("", include("src.content.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
