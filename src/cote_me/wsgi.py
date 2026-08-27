"""
WSGI config para produção (Gunicorn).
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cote_me.settings.prod")
application = get_wsgi_application()
