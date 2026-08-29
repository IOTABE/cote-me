"""
Utilitários do app cotacoes: envio de e-mails, geração de URLs, lógica de distribuição.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone

from core.tokens import montar_token_assinado
from .models import Cotacao, CotacaoTokenFornecedor, RespostaFornecedor, Pedido, ItemPedido


def distribuir_cotacao(cotacao: Cotacao, apenas_pendentes: bool = False) -> int:
    """
    Para cada item da cotação, encontra fornecedores da categoria
    e cria tokens de acesso único (magic-link) para eles.

    apenas_pendentes=True -> envia somente aos fornecedores que ainda
    não enviaram resposta (preco_unitario > 0) para esta cotação.
    Retorna o número de e-mails de convite enviados.
    """
    from accounts.models import Fornecedor

    enviados = 0
    for item in cotacao.itens.select_related("categoria").all():
        fornecedores = Fornecedor.objects.filter(
            ativo=True,
            categorias=item.categoria,
            user__is_active=True,
        ).select_related("user")

        for forn in fornecedores:
            if apenas_pendentes and RespostaFornecedor.objects.filter(
                item__cotacao=cotacao,
                fornecedor=forn.user,
                preco_unitario__gt=0,
            ).exists():
                continue
            # Cria resposta vazia (placeholder) para este fornecedor+item
            RespostaFornecedor.objects.get_or_create(
                item=item,
                fornecedor=forn.user,
                defaults={"preco_unitario": 0, "prazo_entrega_dias": 0},
            )
            # Cria token de acesso (um por fornecedor por cotação)
            token_obj, _created = CotacaoTokenFornecedor.objects.get_or_create(
                cotacao=cotacao,
                fornecedor=forn.user,
                defaults={"token_hash": montar_token_assinado()},
            )
            # Envia e-mail de convite
            _enviar_convite_fornecedor(token_obj)
            enviados += 1

    return enviados


def _enviar_convite_fornecedor(token: CotacaoTokenFornecedor) -> None:
    """Envia e-mail de convite para o fornecedor responder a cotação."""
    url = montar_url_resposta_fornecedor(token)
    assunto = f"[cote-me] Nova cotação #{token.cotacao.id} — {token.cotacao.itens.first().categoria.nome}"
    contexto = {
        "cotacao": token.cotacao,
        "fornecedor": token.fornecedor.fornecedor_profile,
        "url": url,
        "prazo_limite": token.cotacao.prazo_limite,
    }
    corpo_html = render_to_string("cotacoes/email_convite_fornecedor.html", contexto)
    corpo_texto = strip_tags(corpo_html)
    send_mail(
        assunto,
        corpo_texto,
        settings.DEFAULT_FROM_EMAIL,
        [token.fornecedor.email],
        html_message=corpo_html,
        fail_silently=False,
    )


def montar_url_resposta_fornecedor(token: CotacaoTokenFornecedor) -> str:
    """Gera URL absoluta para o fornecedor responder (link único)."""
    from django.urls import reverse
    path = reverse("fornecedor:responder", args=[token.cotacao.id, token.token_hash])
    return f"{settings.BASE_URL}{path}"


def notificar_cliente_nova_resposta(cotacao: Cotacao) -> None:
    """Envia e-mail ao cliente informando nova resposta recebida."""
    url = f"{settings.BASE_URL}/cliente/cotacoes/{cotacao.id}/"
    assunto = f"[cote-me] Nova resposta na cotação #{cotacao.id}"
    contexto = {"cotacao": cotacao, "url": url}
    corpo_html = render_to_string("cotacoes/email_nova_resposta_cliente.html", contexto)
    corpo_texto = strip_tags(corpo_html)
    send_mail(
        assunto,
        corpo_texto,
        settings.DEFAULT_FROM_EMAIL,
        [cotacao.cliente.email],
        html_message=corpo_html,
        fail_silently=False,
    )


def notificar_fornecedor_pedido(pedido: Pedido) -> None:
    """Envia e-mail ao fornecedor com o pedido confirmado."""
    url = f"{settings.BASE_URL}/fornecedor/pedidos/{pedido.id}/"
    assunto = f"[cote-me] Novo pedido #{pedido.id} — {pedido.fornecedor.fornecedor_profile.get_display_name()}"
    contexto = {"pedido": pedido, "url": url}
    corpo_html = render_to_string("cotacoes/email_pedido_fornecedor.html", contexto)
    corpo_texto = strip_tags(corpo_html)
    send_mail(
        assunto,
        corpo_texto,
        settings.DEFAULT_FROM_EMAIL,
        [pedido.fornecedor.email],
        html_message=corpo_html,
        fail_silently=False,
    )


def gerar_pedidos_automaticos(cotacao: Cotacao, escolhas: dict[int, int]) -> list[Pedido]:
    """
    Cria pedidos agrupados por fornecedor a partir das escolhas do cliente.
    escolhas = {item_cotacao_id: resposta_fornecedor_id}
    Retorna lista de Pedidos criados.
    """
    # Agrupa itens por fornecedor vencedor
    from collections import defaultdict
    itens_por_fornecedor = defaultdict(list)
    for item_id, resp_id in escolhas.items():
        resp = RespostaFornecedor.objects.select_related("fornecedor", "item").get(id=resp_id)
        itens_por_fornecedor[resp.fornecedor].append((resp.item, resp))

    pedidos = []
    for fornecedor, itens_respostas in itens_por_fornecedor.items():
        pedido = Pedido.objects.create(
            cotacao=cotacao,
            fornecedor=fornecedor,
            status=Pedido.Status.ENVIADO,
            observacoes="",
        )
        for item, resp in itens_respostas:
            ItemPedido.objects.create(
                pedido=pedido,
                item_cotacao=item,
                resposta_vencedora=resp,
                quantidade=item.quantidade,
                preco_unitario=resp.preco_unitario,
            )
        pedido.recalcular_total()
        notificar_fornecedor_pedido(pedido)
        pedidos.append(pedido)

    # Atualiza status da cotação
    cotacao.status = Cotacao.Status.PEDIDO_DISPARADO
    cotacao.save(update_fields=["status"])
    return pedidos