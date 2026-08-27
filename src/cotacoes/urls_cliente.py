"""
URLs do cliente (namespace 'cliente').
"""
from django.urls import path
from . import views_cliente

app_name = "cliente"

urlpatterns = [
    path("", views_cliente.dashboard, name="dashboard"),
    path("nova/", views_cliente.nova_cotacao, name="nova"),
    path("<int:pk>/", views_cliente.detalhe_cotacao, name="detalhe"),
    path("<int:pk>/escolher/", views_cliente.escolher_vencedores, name="escolher_vencedores"),
    path("pedidos/", views_cliente.meus_pedidos, name="meus_pedidos"),
]