"""
Django settings - DESENVOLVIMENTO
- SQLite
- Email em console
- DEBUG=True
- Tokens de link único em texto puro para inspeção
"""
from .base import *  # noqa: F401,F403
import environ

env = environ.Env()
env.read_env(BASE_DIR.parent / ".env")  # noqa: F405

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

# Email em console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Celery em modo eager (sem worker) para dev
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Whitenoise em dev sem compressão para hot-reload
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Em dev, tokens são decodáveis para facilitar debug
TOKEN_HMAC_KEY = "dev-only-key"
