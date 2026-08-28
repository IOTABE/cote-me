"""
Views do CLIENTE: dashboard, criar cotação, detalhar, escolher vencedores, disparar pedidos.
"""
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from .models import Cotacao, ItemCotacao, RespostaFornecedor, Pedido
from .forms import CotacaoForm, ItemCotacaoFormSet, EscolhaVencedorForm, PedidoForm
from .utils import distribuir_cotacao, gerar_pedidos_automaticos


@login_required
@require_http_methods(["GET"])
def dashboard(request):
    """Lista de cotações do cliente com filtros."""
    qs = Cotacao.objects.filter(cliente=request.user).select_related("cliente").order_by("-criada_em")

    status_filtro = request.GET.get("status")
    if status_filtro:
        qs = qs.filter(status=status_filtro)

    return render(request, "cotacoes/cliente/dashboard.html", {
        "cotacoes": qs,
        "status_filtro": status_filtro,
        "status_choices": Cotacao.Status.choices,
    })


@login_required
@require_http_methods(["GET", "POST"])
def nova_cotacao(request):
    """Cria nova cotação com múltiplos itens."""
    if request.method == "POST":
        form = CotacaoForm(request.POST)
        formset = ItemCotacaoFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            cotacao = form.save(commit=False)
            cotacao.cliente = request.user
            cotacao.status = Cotacao.Status.ABERTA
            cotacao.save()
            formset.instance = cotacao
            formset.save()
            # Dispara e-mails para fornecedores
            total_tokens = distribuir_cotacao(cotacao)
            messages.success(
                request,
                f"Cotação #{cotacao.id} criada! "
                f"Convites enviados para {total_tokens} fornecedor(es)."
            )
            return redirect("cliente:detalhe", pk=cotacao.pk)
    else:
        form = CotacaoForm()
        formset = ItemCotacaoFormSet()

    return render(request, "cotacoes/cliente/nova.html", {
        "form": form,
        "formset": formset,
    })


@login_required
@require_http_methods(["GET"])
def detalhe_cotacao(request, pk):
    """Detalhe da cotação: itens, respostas, comparação (se fechada)."""
    cotacao = get_object_or_404(
        Cotacao.objects.select_related("cliente").prefetch_related(
            "itens__categoria",
            "itens__respostas_fornecedor__fornecedor__fornecedor_profile",
        ),
        pk=pk,
        cliente=request.user,
    )

    # Para cada item, prepara lista de respostas ordenadas por preço
    itens_com_respostas = []
    for item in cotacao.itens.all():
        respostas = list(item.respostas_fornecedor.select_related("fornecedor__fornecedor_profile").order_by("preco_unitario"))
        melhor = respostas[0] if respostas else None
        itens_com_respostas.append({
            "item": item,
            "respostas": respostas,
            "melhor": melhor,
        })

    return render(request, "cotacoes/cliente/detalhe.html", {
        "cotacao": cotacao,
        "itens_com_respostas": itens_com_respostas,
    })


@login_required
@require_http_methods(["GET", "POST"])
def escolher_vencedores(request, pk):
    """Cliente escolhe o vencedor de cada item (após cotação FECHADA)."""
    cotacao = get_object_or_404(Cotacao, pk=pk, cliente=request.user)

    if cotacao.status != Cotacao.Status.FECHADA:
        messages.error(request, "Só é possível escolher vencedores após o fechamento da cotação.")
        return redirect("cliente:detalhe", pk=pk)

    if request.method == "POST":
        escolhas = {}
        for item in cotacao.itens.all():
            vencedor_id = request.POST.get(f"vencedor_{item.id}")
            if vencedor_id:
                try:
                    escolhas[item.id] = int(vencedor_id)
                except ValueError:
                    pass

        if not escolhas:
            messages.error(request, "Selecione ao menos um vencedor.")
        else:
            pedidos = gerar_pedidos_automaticos(cotacao, escolhas)
            messages.success(
                request,
                f"Pedidos gerados! {len(pedidos)} pedido(s) enviado(s) aos fornecedores vencedores."
            )
            return redirect("cliente:detalhe", pk=pk)

    # GET: prepara formulários por item
    forms_por_item = []
    for item in cotacao.itens.all():
        form = EscolhaVencedorForm(item_cotacao=item)
        forms_por_item.append({"item": item, "form": form})

    return render(request, "cotacoes/cliente/escolher_vencedores.html", {
        "cotacao": cotacao,
        "forms_por_item": forms_por_item,
    })


@login_required
@require_http_methods(["GET"])
def meus_pedidos(request):
    """Lista pedidos gerados a partir das cotações do cliente."""
    pedidos = Pedido.objects.filter(
        cotacao__cliente=request.user
    ).select_related(
        "cotacao", "fornecedor__fornecedor_profile"
    ).prefetch_related("itens__item_cotacao").order_by("-criado_em")

    return render(request, "cotacoes/cliente/meus_pedidos.html", {
        "pedidos": pedidos,
    })