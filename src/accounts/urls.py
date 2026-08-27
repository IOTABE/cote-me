"""
URLs de autenticação.
"""
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("cadastro/", views.cliente_cadastro, name="cliente_cadastro"),
    path("confirmar/", views.confirmar_email, name="confirmar_email"),
    path("login/", views.cliente_login, name="cliente_login"),
    path("fornecedor/login/", views.fornecedor_login, name="fornecedor_login"),
    path("fornecedor/primeiro-acesso/", views.fornecedor_primeiro_acesso, name="fornecedor_primeiro_acesso"),
    path("logout/", views.logout_view, name="logout"),
]