"""
Modelos de usuário: Cliente e Fornecedor.

Estratégia: User (Django) + OneToOne profiles.
- Cliente: qualquer pessoa pode se cadastrar + confirmação por e-mail.
- Fornecedor: cadastrado pelo admin; recebe senha temporária por e-mail.
"""
from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """Usuário base. Tipo definido pelo profile (Cliente/Fornecedor)."""
    email = models.EmailField(unique=True)
    telefone = models.CharField(max_length=30, blank=True, default="")
    aceitou_termos = models.BooleanField(default=False)
    aceitou_termos_em = models.DateTimeField(null=True, blank=True)

    groups = models.ManyToManyField(
        "auth.Group",
        verbose_name="groups",
        blank=True,
        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
        related_name="custom_user_set",
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        "auth.Permission",
        verbose_name="user permissions",
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="custom_user_set",
        related_query_name="user",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"


class Cliente(models.Model):
    """Perfil de cliente (solicitante de cotação)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cliente_profile",
        primary_key=True,
    )
    empresa = models.CharField(max_length=200, blank=True, default="")
    cnpj = models.CharField(max_length=18, blank=True, default="", help_text="Opcional")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return self.user.get_full_name() or self.user.email


class Fornecedor(models.Model):
    """Perfil de fornecedor (responde cotações)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fornecedor_profile",
        primary_key=True,
    )
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True, default="")
    cnpj = models.CharField(max_length=18, unique=True)
    telefone = models.CharField(max_length=30, blank=True, default="")
    endereco = models.TextField(blank=True, default="")
    categorias = models.ManyToManyField("core.Categoria", related_name="fornecedores", blank=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    primeiro_acesso = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"

    def __str__(self) -> str:
        return self.nome_fantasia or self.razao_social

    def get_display_name(self) -> str:
        return self.nome_fantasia or self.razao_social