"""
Management command: fecha cotações com prazo expirado.
Útil em dev/CI onde não há Celery.
Em produção, agendar via Celery Beat.
"""
from django.core.management.base import BaseCommand

from core.tasks import fechar_cotacoes_expiradas


class Command(BaseCommand):
    help = "Fecha cotações com prazo expirado (sincronamente)."

    def handle(self, *args, **options):
        total = fechar_cotacoes_expiradas()
        self.stdout.write(self.style.SUCCESS(f"{total} cotação(ões) fechada(s)."))
