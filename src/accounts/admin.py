"""
Admin do app accounts.
Como o projeto usa um modelo de usuário customizado (accounts.User),
é preciso registrá-lo manualmente no admin (o UserAdmin padrão do
django.contrib.auth só registra o modelo quando AUTH_USER_MODEL == 'auth.User').
"""
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

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
    list_display = (
        "razao_social",
        "nome_fantasia",
        "cnpj",
        "email_fornecedor",
        "categorias_display",
        "ativo",
        "criado_em",
    )
    list_filter = ("ativo", "categorias", "criado_em")
    search_fields = ("razao_social", "nome_fantasia", "cnpj", "user__email")
    readonly_fields = ("criado_em", "primeiro_acesso")
    filter_horizontal = ("categorias",)
    actions = ["aprovar_fornecedores", "reprovar_fornecedores"]

    fieldsets = (
        (None, {
            "fields": ("razao_social", "nome_fantasia", "cnpj"),
        }),
        ("Contato", {
            "fields": ("telefone", "endereco"),
        }),
        ("Atuação", {
            "fields": ("categorias",),
        }),
        ("Status", {
            "fields": ("ativo", "criado_em", "primeiro_acesso"),
            "description": "Marque 'ativo' para aprovar o fornecedor e permitir que receba cotações.",
        }),
    )

    def email_fornecedor(self, obj):
        return obj.user.email
    email_fornecedor.short_description = "E-mail"
    email_fornecedor.admin_order_field = "user__email"

    def categorias_display(self, obj):
        cats = obj.categorias.values_list("nome", flat=True)
        return ", ".join(cats) if cats else "—"
    categorias_display.short_description = "Categorias"

    @admin.action(description="Aprovar fornecedor(es) selecionado(s)")
    def aprovar_fornecedores(self, request, queryset):
        aprovados = 0
        for fornecedor in queryset.select_related("user"):
            if not fornecedor.ativo:
                fornecedor.ativo = True
                fornecedor.save(update_fields=["ativo"])
                # Ativa o user caso esteja inativo (após confirmar email)
                if not fornecedor.user.is_active:
                    fornecedor.user.is_active = True
                    fornecedor.user.save(update_fields=["is_active"])
                # Notifica por email
                self._notificar_aprovacao(fornecedor)
                aprovados += 1
        messages.success(request, f"{aprovados} fornecedor(es) aprovado(s) e notificado(s) por e-mail.")

    @admin.action(description="Reprovar fornecedor(es) selecionado(s)")
    def reprovar_fornecedores(self, request, queryset):
        reprovados = 0
        for fornecedor in queryset.select_related("user"):
            if fornecedor.ativo:
                fornecedor.ativo = False
                fornecedor.save(update_fields=["ativo"])
                reprovados += 1
        messages.success(request, f"{reprovados} fornecedor(es) reprovado(s).")

    def _notificar_aprovacao(self, fornecedor):
        """Envia e-mail ao fornecedor informando que foi aprovado."""
        try:
            assunto = "[cote-me] Seu cadastro foi aprovado!"
            url_login = f"{settings.BASE_URL}/conta/fornecedor/login/"
            corpo_html = (
                f"<p>Olá <strong>{fornecedor.get_display_name()}</strong>,</p>"
                f"<p>Seu cadastro na plataforma <strong>cote-me</strong> foi aprovado!</p>"
                f"<p>Agora você pode receber e responder cotações de clientes.</p>"
                f'<p><a href="{url_login}">Acesse sua conta</a></p>'
                f"<p>Equipe cote-me</p>"
            )
            send_mail(
                assunto,
                strip_tags(corpo_html),
                settings.DEFAULT_FROM_EMAIL,
                [fornecedor.user.email],
                html_message=corpo_html,
                fail_silently=True,
            )
        except Exception:
            pass  # não bloqueia a aprovação se o email falhar
