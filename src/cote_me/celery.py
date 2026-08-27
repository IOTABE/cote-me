"""
Inicialização do Celery para tarefas assíncronas.
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cote_me.settings.prod")

app = Celery("cote_me")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
