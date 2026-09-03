"""Production / Droplet: DEBUG=False; HTTP-first (USE_HTTPS=false) або HTTPS після certbot."""
from decouple import Csv, config

from .base import *  # noqa: F401,F403

DEBUG = False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

USE_HTTPS = config("USE_HTTPS", default=False, cast=bool)
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# TLS у nginx; Gunicorn лишається HTTP — інакше healthz → 301 → unhealthy (django-docker-ssl).
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", default=USE_HTTPS, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", default=USE_HTTPS, cast=bool)
SESSION_COOKIE_SAMESITE = "Strict"
CSRF_COOKIE_SAMESITE = "Strict"
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=(31536000 if USE_HTTPS else 0), cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_HSTS_PRELOAD = USE_HTTPS

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="")

LOGGING["handlers"]["console"]["level"] = "WARNING"  # noqa: F405
