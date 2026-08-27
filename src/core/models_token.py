"""
Modelos auxiliares: tokens de uso único (confirmação de e-mail, magic link).
"""
from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailToken(models.Model):
    """Token de uso único para confirmação de e-mail ou magic-link de fornecedor."""

    class Tipo(models.TextChoices):
        CONFIRMACAO_EMAIL = "confirmacao_email", "Confirmação de e-mail"
        MAGIC_LINK_FORNECEDOR = "magic_link_fornecedor", "Magic-link fornecedor"
        OUTRO = "outro", "Outro"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_tokens",
    )
    tipo = models.CharField(max_length=32, choices=Tipo.choices)
    token_hash = models.CharField(max_length=128, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    usado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["token_hash"]),
            models.Index(fields=["user", "tipo"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} · {self.tipo} · {self.token_hash[:8]}…"

    @property
    def valido(self) -> bool:
        if self.usado_em is not None:
            return False
        return timezone.now() < self.expira_em

    def marcar_usado(self) -> None:
        self.usado_em = timezone.now()
        self.save(update_fields=["usado_em"])
