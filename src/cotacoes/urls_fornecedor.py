"""
URLs do fornecedor (namespace 'fornecedor').
"""
from django.urls import path
from . import views_fornecedor

app_name = "fornecedor"

urlpatterns = [
    path("", views_fornecedor.dashboard_fornecedor, name="dashboard"),
    path("responder/<int:cotacao_id>/<str:token_hash>/", views_fornecedor.responder_por_token, name="responder"),
    path("responder/<int:pk>/", views_fornecedor.responder_dashboard, name="responder_dashboard"),
    path("pedidos/<int:pk>/", views_fornecedor.detalhe_pedido, name="detalhe_pedido"),
]