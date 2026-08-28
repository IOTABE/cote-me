"""
Admin do app accounts.
Como o projeto usa um modelo de usuário customizado (accounts.User),
é preciso registrá-lo manualmente no admin (o UserAdmin padrão do
django.contrib.auth só registra o modelo quando AUTH_USER_MODEL == 'auth.User').
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Cliente, Fornecedor


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    pass


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("user", "empresa", "cnpj", "criado_em")
    search_fields = ("user__email", "user__username", "empresa")


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "nome_fantasia", "cnpj", "ativo")
    list_filter = ("ativo",)
    search_fields = ("razao_social", "nome_fantasia", "cnpj")
