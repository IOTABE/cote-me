"""
Django settings - PRODUÇÃO
- PostgreSQL
- SMTP real
- DEBUG=False
- Segurança reforçada
"""
from .base import *  # noqa: F401,F403
import environ
import os

env = environ.Env()
env.read_env(BASE_DIR.parent / ".env")  # noqa: F405

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["cote-me.example.com"])
if not ALLOWED_HOSTS:
    raise RuntimeError("ALLOWED_HOSTS must be set in production")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", default="cote_me"),
        "USER": env("DB_USER", default="cote_me"),
        "PASSWORD": env("DB_PASSWORD", default=""),
        "HOST": env("DB_HOST", default="localhost"),
        "PORT": env("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
    }
}

# Cookies e HTTPS
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # 30 dias
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@cote-me.example.com")

# Token em produção - chave secreta obrigatória
TOKEN_HMAC_KEY = env("TOKEN_HMAC_KEY")
if not TOKEN_HMAC_KEY or TOKEN_HMAC_KEY == "change-me-hmac-key-in-production":
    raise RuntimeError("TOKEN_HMAC_KEY must be set in production")
