"""Налаштування для тестів: швидкі хешери паролів, in-memory поштова скринька."""
from .base import *  # noqa: F401,F403

DEBUG = False
SECRET_KEY = "test-secret-key"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Без Manifest — інакше {% static %} у тестах падає без collectstatic
STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
