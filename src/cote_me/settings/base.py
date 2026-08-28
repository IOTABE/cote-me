"""
Django settings - base compartilhado entre dev e prod.
Nunca usar diretamente; importar de .dev ou .prod.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-CHANGE-ME-IN-PRODUCTION-9d8f7g6h5j4k3l2m1n0b9v8c7x6z5a4s3d2f1g",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS: list[str] = []

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "django_extensions",
    # local
    "accounts.apps.AccountsConfig",
    "core.apps.CoreConfig",
    "cotacoes.apps.CotacoesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "cote_me.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cote_me.wsgi.application"
ASGI_APPLICATION = "cote_me.asgi.application"

# Database - definido em dev/prod
DATABASES = {}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# HASH de senha mais forte (argon2)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

# Auth - login próprio
AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/conta/login/"

# URL base usada em links de e-mail (confirmação, cotações, pedidos)
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000")
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email - backend configurado em dev/prod
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "cote-me <noreply@cote-me.local>"

# Celery
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = False

# Tokens / links únicos
TOKEN_HMAC_KEY = os.environ.get("TOKEN_HMAC_KEY", "change-me-hmac-key-in-production")
TOKEN_VALIDADE_HORAS = 24
TOKEN_COTACAO_VALIDADE_HORAS = 24 * 7  # até o prazo da cotação + margem

# Prazo de cotação padrão
COTACAO_PRAZO_PADRAO_HORAS = 48
COTACAO_PRAZO_MIN_HORAS = 1
COTACAO_PRAZO_MAX_DIAS = 30

# Whitenoise
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
