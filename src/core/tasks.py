"""
Tarefas Celery / management commands de manutenção.

Como rodar no dev (sem celery):
    uv run python manage.py fechar_cotacoes
    uv run python manage.py enviar_lembretes

Em produção (com Celery + Beat), as tarefas abaixo são agendadas.
"""
from __future__ import annotations
import logging
from datetime import timedelta

from celery import shared_task
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(name="cotacoes.fechar_cotacoes_expiradas")
def fechar_cotacoes_expiradas() -> int:
    """Marca como FECHADA toda cotação com prazo vencido e notifica o cliente."""
    from cotacoes.models import Cotacao

    agora = timezone.now()
    qs = Cotacao.objects.filter(
        status__in=[Cotacao.Status.ABERTA, Cotacao.Status.PARCIAL],
        prazo_limite__lt=agora,
    )
    total = 0
    for cotacao in qs:
        cotacao.status = Cotacao.Status.FECHADA
        cotacao.fechada_em = agora
        cotacao.save(update_fields=["status", "fechada_em"])
        _notificar_cliente_cotacao_fechada(cotacao)
        total += 1
    if total:
        logger.info("Fechadas %d cotação(ões) expirada(s).", total)
    return total


@shared_task(name="cotacoes.enviar_lembrete_fornecedor")
def enviar_lembrete_fornecedor() -> int:
    """Envia 1 lembrete por dia a fornecedores que ainda não responderam (>=50% do prazo)."""
    from cotacoes.models import Cotacao, RespostaFornecedor
    from cotacoes.utils import montar_url_resposta_fornecedor

    agora = timezone.now()
    enviadas = 0
    cotacoes = Cotacao.objects.filter(
        status__in=[Cotacao.Status.ABERTA, Cotacao.Status.PARCIAL],
    )
    for cot in cotacoes:
        if not cot.prazo_limite:
            continue
        duracao = cot.prazo_limite - cot.criada_em
        meio_prazo = cot.criada_em + duracao / 2
        if agora < meio_prazo:
            continue
        # encontra tokens ainda não usados para esta cotação
        tokens = cot.tokens_fornecedor.filter(usado_em__isnull=True).select_related("fornecedor")
        for tk in tokens:
            url = montar_url_resposta_fornecedor(tk)
            _enviar_email(
                subject=f"[cote-me] Lembrete: cotação #{cot.id} aguardando resposta",
                template="cotacoes/email_lembrete_fornecedor.txt",
                contexto={"cotacao": cot, "url": url, "fornecedor": tk.fornecedor},
                destinatario=tk.fornecedor.email,
            )
            enviadas += 1
    return enviadas


def _enviar_email(subject: str, template: str, contexto: dict, destinatario: str) -> None:
    corpo_html = render_to_string(template, contexto)
    corpo_texto = strip_tags(corpo_html)
    from django.core.mail import send_mail
    send_mail(
        subject=subject,
        message=corpo_texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[destinatario],
        html_message=corpo_html,
        fail_silently=False,
    )


def _notificar_cliente_cotacao_fechada(cotacao) -> None:
    _enviar_email(
        subject=f"[cote-me] Cotação #{cotacao.id} fechada — compare preços",
        template="cotacoes/email_cotacao_fechada.txt",
        contexto={"cotacao": cotacao},
        destinatario=cotacao.cliente.email,
    )
