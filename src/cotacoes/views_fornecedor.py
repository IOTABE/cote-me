"""
Views do FORNECEDOR: dashboard, responder cotação (via link ou dashboard), ver pedidos.
"""
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils import timezone

from core.tokens import validar_token_assinado
from .models import Cotacao, CotacaoTokenFornecedor, RespostaFornecedor, ItemCotacao, Pedido, ItemPedido
from .forms import RespostaFornecedorForm, get_resposta_formset
from .utils import notificar_cliente_nova_resposta


def _get_fornecedor_profile(user):
    """Helper: retorna o perfil de fornecedor do user ou None."""
    try:
        return user.fornecedor_profile
    except AttributeError:
        return None


@login_required
@require_http_methods(["GET"])
def dashboard_fornecedor(request):
    """Dashboard do fornecedor: cotações pendentes, respondidas, pedidos."""
    profile = _get_fornecedor_profile(request.user)
    if not profile:
        messages.error(request, "Acesso restrito a fornecedores.")
        return redirect("accounts:fornecedor_login")

    # Cotações onde este fornecedor tem tokens válidos
    tokens_pendentes = CotacaoTokenFornecedor.objects.filter(
        fornecedor=request.user,
        usado_em__isnull=True,
    ).select_related("cotacao", "cotacao__cliente").order_by("-cotacao__prazo_limite")

    # Cotações já respondidas (pelo menos 1 item)
    cotacoes_respondidas = Cotacao.objects.filter(
        itens__respostas_fornecedor__fornecedor=request.user,
    ).distinct().select_related("cliente").order_by("-criada_em")

    # Pedidos recebidos
    pedidos = Pedido.objects.filter(
        fornecedor=request.user
    ).select_related("cotacao").prefetch_related("itens__item_cotacao").order_by("-criado_em")

    return render(request, "cotacoes/fornecedor/dashboard.html", {
        "tokens_pendentes": tokens_pendentes,
        "cotacoes_respondidas": cotacoes_respondidas,
        "pedidos": pedidos,
    })


@require_http_methods(["GET", "POST"])
def responder_por_token(request, cotacao_id, token_hash):
    """
    Resposta via magic-link (sem login obrigatório).
    Valida token, mostra formulário, salva resposta.
    """
    # Valida token
    valido, _ = validar_token_assinado(token_hash)
    if not valido:
        messages.error(request, "Link inválido ou expirado.")
        return render(request, "cotacoes/fornecedor/token_invalido.html", status=400)

    try:
        token = CotacaoTokenFornecedor.objects.select_related(
            "cotacao", "fornecedor__fornecedor_profile"
        ).get(cotacao_id=cotacao_id, token_hash=token_hash)
    except CotacaoTokenFornecedor.DoesNotExist:
        messages.error(request, "Token não encontrado.")
        return render(request, "cotacoes/fornecedor/token_invalido.html", status=404)

    if not token.valido:
        messages.error(request, "Este link expirou ou a cotação não está mais aberta.")
        return render(request, "cotacoes/fornecedor/token_invalido.html", status=400)

    cotacao = token.cotacao
    # Itens desta cotação que pertencem às categorias do fornecedor
    itens = ItemCotacao.objects.filter(
        cotacao=cotacao,
        categoria__in=token.fornecedor.fornecedor_profile.categorias.all(),
    ).select_related("categoria").order_by("ordem")

    if not itens.exists():
        messages.info(request, "Nenhum item desta cotação pertence às suas categorias.")
        return render(request, "cotacoes/fornecedor/sem_itens.html")

    itens_list = list(itens)

    if request.method == "POST":
        formset = get_resposta_formset(itens, data=request.POST, fornecedor=token.fornecedor)
        if formset.is_valid():
            for i, form in enumerate(formset):
                if form.has_changed() and i < len(itens_list):
                    resp, _created = RespostaFornecedor.objects.update_or_create(
                        item=itens_list[i],
                        fornecedor=token.fornecedor,
                        defaults={
                            "preco_unitario": form.cleaned_data["preco_unitario"],
                            "prazo_entrega_dias": form.cleaned_data.get("prazo_entrega_dias", 0),
                            "marca": form.cleaned_data.get("marca", ""),
                            "observacoes": form.cleaned_data.get("observacoes", ""),
                        },
                    )
            # Marca token como usado
            token.usado_em = timezone.now()
            token.save(update_fields=["usado_em"])
            # Atualiza status da cotação
            if cotacao.status == Cotacao.Status.ABERTA:
                cotacao.status = Cotacao.Status.PARCIAL
                cotacao.save(update_fields=["status"])
            # Notifica cliente
            notificar_cliente_nova_resposta(cotacao)
            messages.success(request, "Resposta enviada com sucesso!")
            return render(request, "cotacoes/fornecedor/resposta_sucesso.html", {"cotacao": cotacao})
    else:
        formset = get_resposta_formset(itens_list, fornecedor=token.fornecedor)

    # Adiciona referência ao item para exibição no template
    for i, form in enumerate(formset.forms):
        form.item = itens_list[i]

    return render(request, "cotacoes/fornecedor/responder.html", {
        "cotacao": cotacao,
        "token": token,
        "formset": formset,
        "itens": itens_list,
    })


@login_required
@require_http_methods(["GET", "POST"])
def responder_dashboard(request, pk):
    """Resposta via dashboard (fornecedor logado)."""
    profile = _get_fornecedor_profile(request.user)
    if not profile:
        messages.error(request, "Acesso restrito a fornecedores.")
        return redirect("accounts:fornecedor_login")

    cotacao = get_object_or_404(Cotacao, pk=pk)
    # Verifica se fornecedor tem token válido para esta cotação
    token = CotacaoTokenFornecedor.objects.filter(
        cotacao=cotacao,
        fornecedor=request.user,
        usado_em__isnull=True,
    ).first()

    if not token:
        messages.error(request, "Você não tem acesso a esta cotação.")
        return redirect("fornecedor:dashboard")

    # Mesmo fluxo do token
    return responder_por_token(request, pk, token.token_hash)


@login_required
@require_http_methods(["GET"])
def detalhe_pedido(request, pk):
    """Fornecedor vê detalhe do pedido recebido."""
    profile = _get_fornecedor_profile(request.user)
    if not profile:
        messages.error(request, "Acesso restrito a fornecedores.")
        return redirect("accounts:fornecedor_login")

    pedido = get_object_or_404(
        Pedido.objects.select_related("cotacao", "fornecedor__fornecedor_profile")
        .prefetch_related("itens__item_cotacao__categoria", "itens__resposta_vencedora"),
        pk=pk,
        fornecedor=request.user,
    )

    return render(request, "cotacoes/fornecedor/detalhe_pedido.html", {
        "pedido": pedido,
    })