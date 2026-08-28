"""
Views de autenticação: cadastro cliente, login/logout, primeiro acesso fornecedor.
"""
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .forms import (
    ClienteCadastroForm,
    FornecedorCadastroForm,
    ClienteLoginForm,
    FornecedorLoginForm,
    FornecedorAlterarSenhaForm,
)
from .models import User, Fornecedor, Cliente
from core.tokens import montar_token_assinado
from core.models_token import EmailToken


@require_http_methods(["GET", "POST"])
def cliente_cadastro(request):
    """Cadastro público do cliente com envio de e-mail de confirmação."""
    if request.user.is_authenticated:
        return redirect("cliente:dashboard")

    if request.method == "POST":
        form = ClienteCadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Cria token de confirmação
            token = montar_token_assinado()
            EmailToken.objects.create(
                user=user,
                tipo=EmailToken.Tipo.CONFIRMACAO_EMAIL,
                token_hash=token,
                expira_em=timezone.now() + timezone.timedelta(hours=24),
            )
            _enviar_email_confirmacao(user, token)
            messages.success(
                request,
                "Cadastro realizado! Enviamos um e-mail de confirmação. "
                "Verifique sua caixa de entrada (e spam). O link expira em 24h."
            )
            return redirect("accounts:cliente_login")
    else:
        form = ClienteCadastroForm()

    return render(request, "accounts/cliente_cadastro.html", {"form": form})


def _enviar_email_confirmacao(user: User, token: str) -> None:
    """Envia e-mail de confirmação (em dev imprime no console)."""
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings

    url = f"{settings.BASE_URL}/conta/confirmar/?token={token}"
    assunto = "[cote-me] Confirme seu e-mail"
    corpo = render_to_string("accounts/email_confirmacao.txt", {"user": user, "url": url})
    send_mail(
        assunto,
        corpo,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


@require_http_methods(["GET"])
def confirmar_email(request):
    """Valida token de confirmação de e-mail (cliente ou fornecedor)."""
    token = request.GET.get("token", "").strip()
    if not token:
        messages.error(request, "Token inválido.")
        return redirect("accounts:cliente_cadastro")

    from core.tokens import validar_token_assinado
    valido, parte = validar_token_assinado(token)
    if not valido:
        messages.error(request, "Link inválido ou expirado.")
        return redirect("accounts:cliente_cadastro")

    try:
        tk = EmailToken.objects.select_related("user").get(
            token_hash=token,
            tipo=EmailToken.Tipo.CONFIRMACAO_EMAIL,
        )
    except EmailToken.DoesNotExist:
        messages.error(request, "Token não encontrado.")
        return redirect("accounts:cliente_cadastro")

    if not tk.valido:
        messages.error(request, "Este link já foi usado ou expirou.")
        return redirect("accounts:cliente_cadastro")

    # Ativa usuário e marca token usado
    tk.user.is_active = True
    tk.user.save(update_fields=["is_active"])
    tk.marcar_usado()

    # Detecta se é fornecedor ou cliente para redirecionamento correto
    if hasattr(tk.user, "fornecedor_profile"):
        messages.success(
            request,
            "E-mail confirmado! Seu cadastro será analisado e você receberá "
            "um e-mail quando for aprovado pelo administrador."
        )
        return redirect("accounts:fornecedor_login")

    messages.success(request, "E-mail confirmado! Você já pode fazer login.")
    return redirect("accounts:cliente_login")


@require_http_methods(["GET", "POST"])
def cliente_login(request):
    if request.user.is_authenticated:
        return redirect("cliente:dashboard")

    if request.method == "POST":
        form = ClienteLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not hasattr(user, "cliente_profile"):
                messages.error(request, "Esta conta não é de um cliente.")
                return render(request, "accounts/cliente_login.html", {"form": form})
            login(request, user)
            return redirect("cliente:dashboard")
    else:
        form = ClienteLoginForm()

    return render(request, "accounts/cliente_login.html", {"form": form})


@require_http_methods(["GET", "POST"])
def fornecedor_cadastro(request):
    """Cadastro público de fornecedor (pendente de aprovação do admin)."""
    if request.user.is_authenticated:
        return redirect("core:dashboard_redirect")

    if request.method == "POST":
        form = FornecedorCadastroForm(request.POST)
        if form.is_valid():
            user = form.save()
            token = montar_token_assinado()
            EmailToken.objects.create(
                user=user,
                tipo=EmailToken.Tipo.CONFIRMACAO_EMAIL,
                token_hash=token,
                expira_em=timezone.now() + timezone.timedelta(hours=24),
            )
            _enviar_email_confirmacao(user, token)
            messages.success(
                request,
                "Cadastro realizado! Enviamos um e-mail de confirmação. "
                "Após confirmar, seu cadastro será analisado pelo administrador."
            )
            return redirect("accounts:fornecedor_login")
    else:
        form = FornecedorCadastroForm()

    return render(request, "accounts/fornecedor_cadastro.html", {"form": form})


@require_http_methods(["GET", "POST"])
def fornecedor_login(request):
    if request.user.is_authenticated:
        if hasattr(request.user, "fornecedor_profile"):
            return redirect("fornecedor:dashboard")
        logout(request)
        messages.info(request, "Faça login como fornecedor.")

    if request.method == "POST":
        form = FornecedorLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if not hasattr(user, "fornecedor_profile"):
                messages.error(request, "Esta conta não é de um fornecedor.")
                return render(request, "accounts/fornecedor_login.html", {"form": form})
            login(request, user)
            return redirect("fornecedor:dashboard")
    else:
        form = FornecedorLoginForm()

    return render(request, "accounts/fornecedor_login.html", {"form": form})


@login_required
@require_http_methods(["GET", "POST"])
def fornecedor_primeiro_acesso(request):
    """Fornecedor troca a senha temporária no primeiro login."""
    if not hasattr(request.user, "fornecedor_profile"):
        return redirect("fornecedor:dashboard")

    if request.method == "POST":
        form = FornecedorAlterarSenhaForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            # Marca primeiro acesso
            request.user.fornecedor_profile.primeiro_acesso = timezone.now()
            request.user.fornecedor_profile.save(update_fields=["primeiro_acesso"])
            messages.success(request, "Senha alterada com sucesso!")
            return redirect("fornecedor:dashboard")
    else:
        form = FornecedorAlterarSenhaForm(user=request.user)

    return render(request, "accounts/fornecedor_primeiro_acesso.html", {"form": form})


@require_http_methods(["POST"])
def logout_view(request):
    logout(request)
    messages.info(request, "Você saiu do sistema.")
    return redirect("core:home")