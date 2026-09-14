"""Базові налаштування Django, спільні для всіх середовищ."""
from pathlib import Path

from decouple import Csv, config
from django.urls import reverse_lazy

# config/settings/base.py -> config/settings/ -> config/ -> корінь проєкту
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")  # без default= — production падає без .env
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

INSTALLED_APPS = [
    # 1. Unfold — обов'язково перед django.contrib.admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    # 2. modeltranslation — до admin.autodiscover (TabbedTranslationAdmin)
    "modeltranslation",
    # 3. Django contrib
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    # 4. Сторонні пакети
    "tinymce",
    "django_htmx",
    "csp",
    # 5. Власні apps
    "src.core",
    "src.accounts",
    "src.catalog",
    "src.content",
    "src.pricing",
    "src.commerce",
    "src.shipping",
    "src.seo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "src.content.middleware.DisabledLanguageRedirectMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "src.commerce.context_processors.cart_badge",
                "src.content.context_processors.site_settings",
                "src.catalog.context_processors.nav_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="nanesi"),
        "USER": config("POSTGRES_USER", default="nanesi"),
        "PASSWORD": config("POSTGRES_PASSWORD", default=""),
        "HOST": config("POSTGRES_HOST", default="localhost"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

# --- Кабінет (Підетап 2, Відповіді п.6): вхід за телефоном або email, одна форма ---
AUTHENTICATION_BACKENDS = [
    "src.accounts.backends.PhoneOrEmailBackend",
    "django.contrib.auth.backends.ModelBackend",  # для createsuperuser / входу в адмінку за username
]
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:profile"
LOGOUT_REDIRECT_URL = "catalog:home"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- i18n: uk основна, ru/en увімкнені на старті (тумблер у SiteSettings — Етап D) ---
LANGUAGE_CODE = "uk"
LANGUAGES = [
    ("uk", "Українська"),
    ("ru", "Русский"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
MODELTRANSLATION_DEFAULT_LANGUAGE = "uk"
MODELTRANSLATION_LANGUAGES = ("uk", "ru", "en")
MODELTRANSLATION_FALLBACK_LANGUAGES = {"default": ("uk",)}

TIME_ZONE = "Europe/Kyiv"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # whitenoise: content-hash у імені файлу + gzip/brotli — кеш без ручного бампу версій
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

ADMIN_URL = config("ADMIN_URL", default="admin/")

# --- Нова Пошта (novaposhta_skill): порожній ключ = інтеграція вимкнена, без stub-даних ---
NP_API_KEY = config("NP_API_KEY", default="")
NP_SENDER_REF = config("NP_SENDER_REF", default="")
NP_SENDER_CONTACT_REF = config("NP_SENDER_CONTACT_REF", default="")
NP_SENDER_CITY_REF = config("NP_SENDER_CITY_REF", default="")
NP_SENDER_ADDRESS_REF = config("NP_SENDER_ADDRESS_REF", default="")
NP_SENDER_PHONE = config("NP_SENDER_PHONE", default="")

# --- LiqPay (liqpay_skill) — порожні ключі = "оплата карткою" прибирається з checkout ---
LIQPAY_PUBLIC_KEY = config("LIQPAY_PUBLIC_KEY", default="")
LIQPAY_PRIVATE_KEY = config("LIQPAY_PRIVATE_KEY", default="")
LIQPAY_SERVER_URL = config("LIQPAY_SERVER_URL", default="")
LIQPAY_SANDBOX = config("LIQPAY_SANDBOX", default=True, cast=bool)

# --- TinyMCE (admin_skill канон) ---
# Enter → <br> (linebreak), щоб переноси були видимі на вітрині без CSS white-space.
# setup: під час завантаження контенту «голі» \n → <br> (paste / старі дані).
TINYMCE_DEFAULT_CONFIG = {
    "height": 400,
    "menubar": False,
    "plugins": "link lists image code paste",
    "toolbar": "undo redo | bold italic underline | bullist numlist | link image | code",
    "content_css": False,
    "skin": "oxide",
    "forced_root_block": "p",
    "newline_behavior": "linebreak",
    "remove_trailing_brs": False,
    "paste_preprocess": (
        "function(plugin, args){"
        "if(!args.content)return;"
        "var c=args.content.replace(/\\r\\n/g,'\\n').replace(/\\r/g,'\\n');"
        "if(c.indexOf('<')===-1){args.content=c.replace(/\\n/g,'<br>');}"
        "}"
    ),
    "setup": (
        "function(editor){"
        "editor.on('BeforeSetContent',function(e){"
        "if(!e.content||e.content.indexOf('\\n')===-1)return;"
        "var c=e.content.replace(/\\r\\n/g,'\\n').replace(/\\r/g,'\\n');"
        "if(!/<(?:p|br|div|li|h[1-6]|ul|ol|table)\\b/i.test(c)){"
        "e.content=c.trim().split(/\\n{2,}/).map(function(p){"
        "return '<p>'+p.replace(/\\n/g,'<br>')+'</p>';"
        "}).join('');"
        "return;"
        "}"
        "e.content=c.split(/(<[^>]+>)/).map(function(part){"
        "if(!part||part.charAt(0)==='<')return part;"
        "if(!part.trim())return part.replace(/\\n/g,'');"
        "return part.replace(/\\n/g,'<br>');"
        "}).join('');"
        "});"
        "}"
    ),
}

# --- CSP (django-csp 4.0): адмінка (Unfold/Alpine.js) виключена — потребує unsafe-eval ---
# Домени GTM/GA4/Meta/TikTok додані заздалегідь (Доповнення §1 «Пікселі») — щоб увімкнення
# ID у SiteSettings з адмінки не вимагало деплою; самі скрипти вантажаться лише якщо ID заданий
# (static/js/analytics.js), а не інлайн — тож 'unsafe-inline' тут не потрібен.
CONTENT_SECURITY_POLICY = {
    "EXCLUDE_URL_PREFIXES": ("/admin/",),
    "DIRECTIVES": {
        "default-src": ["'self'"],
        "script-src": [
            "'self'",
            "https://www.googletagmanager.com",
            "https://connect.facebook.net",
            "https://analytics.tiktok.com",
        ],
        "style-src": ["'self'", "https://fonts.googleapis.com"],
        "font-src": ["'self'", "https://fonts.gstatic.com"],
        "img-src": [
            "'self'", "data:",
            "https://www.facebook.com",
            "https://www.google-analytics.com",
            "https://analytics.tiktok.com",
        ],
        "connect-src": [
            "'self'",
            "https://www.googletagmanager.com",
            "https://www.google-analytics.com",
            "https://*.google-analytics.com",
            "https://*.analytics.google.com",
            "https://www.facebook.com",
            "https://analytics.tiktok.com",
        ],
        "frame-src": ["https://www.googletagmanager.com"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
    },
}

# --- django-unfold ---
UNFOLD = {
    "SITE_TITLE": "NANESI",
    "SITE_HEADER": "NANESI — Адмінпанель",
    "SITE_SYMBOL": "storefront",
    "SIDEBAR": {
        "show_search": True,
        "command_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Каталог",
                "separator": True,
                "items": [
                    {"title": "Товари", "icon": "inventory_2", "link": reverse_lazy("admin:catalog_product_changelist")},
                    {"title": "Варіанти (SKU)", "icon": "qr_code_2", "link": reverse_lazy("admin:catalog_productvariant_changelist")},
                    {"title": "Категорії", "icon": "category", "link": reverse_lazy("admin:catalog_category_changelist")},
                    {"title": "Бренди", "icon": "sell", "link": reverse_lazy("admin:catalog_brand_changelist")},
                    {"title": "Атрибути", "icon": "tune", "link": reverse_lazy("admin:catalog_attribute_changelist")},
                    {"title": "Значення атрибутів", "icon": "label", "link": reverse_lazy("admin:catalog_attributevalue_changelist")},
                    {"title": "Постачальники", "icon": "local_shipping", "link": reverse_lazy("admin:catalog_supplier_changelist")},
                    {"title": "Підбірки", "icon": "collections_bookmark", "link": reverse_lazy("admin:catalog_collection_changelist")},
                    {"title": "Відгуки", "icon": "reviews", "link": reverse_lazy("admin:catalog_review_changelist")},
                ],
            },
            {
                "title": "Замовлення",
                "separator": True,
                "items": [
                    {"title": "Замовлення", "icon": "shopping_cart", "link": reverse_lazy("admin:commerce_order_changelist")},
                    {"title": "Промокоди", "icon": "local_offer", "link": reverse_lazy("admin:commerce_promocode_changelist")},
                    {"title": "Правила націнки", "icon": "percent", "link": reverse_lazy("admin:pricing_markuprule_changelist")},
                ],
            },
            {
                "title": "Клієнти",
                "separator": True,
                "items": [
                    {"title": "Користувачі", "icon": "group", "link": reverse_lazy("admin:accounts_user_changelist")},
                ],
            },
            {
                "title": "Контент",
                "separator": True,
                "items": [
                    {"title": "Налаштування сайту", "icon": "settings", "link": reverse_lazy("admin:content_sitesettings_change", args=[1])},
                    {"title": "Банери головної", "icon": "view_carousel", "link": reverse_lazy("admin:content_herobanner_changelist")},
                    {"title": "Сторінки", "icon": "description", "link": reverse_lazy("admin:content_staticpage_changelist")},
                    {"title": "Блог", "icon": "article", "link": reverse_lazy("admin:content_blogpost_changelist")},
                    {"title": "Email-ліди (підписки)", "icon": "mail", "link": reverse_lazy("admin:content_newsletterlead_changelist")},
                    {"title": "Переваги (головна)", "icon": "verified", "link": reverse_lazy("admin:content_trustbadge_changelist")},
                ],
            },
        ],
    },
}

# --- Logging з першого дня ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {asctime} {module} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "src": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
