"""
Views do app core: home, about, etc.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def home(request):
    """Landing page pública."""
    return render(request, "core/home.html")


@login_required
def dashboard_redirect(request):
    """Redireciona para o dashboard correto baseado no tipo de usuário."""
    if hasattr(request.user, "cliente_profile"):
        return redirect("cliente:dashboard")
    elif hasattr(request.user, "fornecedor_profile"):
        return redirect("fornecedor:dashboard")
    return render(request, "core/dashboard_redirect.html")