"""
URLs do app core.
"""
from django.urls import path
from django.contrib.auth.decorators import login_required
from django.views.generic import RedirectView
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", login_required(views.dashboard_redirect), name="dashboard_redirect"),
    path("manifest.json", views.manifest_json, name="manifest"),
    path("sw.js", views.service_worker, name="service_worker"),
]