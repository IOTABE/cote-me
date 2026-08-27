"""
ASGI config (opcional - para deploys assíncronos).
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cote_me.settings.prod")
application = get_asgi_application()
