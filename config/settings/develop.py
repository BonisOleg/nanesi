"""Локальна розробка."""
from decouple import config

from .base import *  # noqa: F401,F403

SECRET_KEY = config("SECRET_KEY", default="dev-only-insecure-key-do-not-use-in-prod")
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "*"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],  # noqa: F405
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING["loggers"]["django"]["level"] = "INFO"  # noqa: F405
