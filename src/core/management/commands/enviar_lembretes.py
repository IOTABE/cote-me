"""
Management command: envia lembretes a fornecedores que ainda não responderam.
Útil em dev/CI onde não há Celery.
Em produção, agendar via Celery Beat.
"""
from django.core.management.base import BaseCommand

from core.tasks import enviar_lembrete_fornecedor


class Command(BaseCommand):
    help = "Envia lembretes a fornecedores que ainda não responderam (sincronamente)."

    def handle(self, *args, **options):
        total = enviar_lembrete_fornecedor()
        self.stdout.write(self.style.SUCCESS(f"{total} lembrete(s) enviado(s)."))