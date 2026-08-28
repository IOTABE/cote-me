"""
Modelos principais do sistema de cotações.

- Cotacao: solicitação do cliente (agrupa itens, define prazo).
- ItemCotacao: cada produto/quantidade dentro da cotação.
- RespostaFornecedor: preço/prazo que cada fornecedor oferece para um item.
- CotacaoTokenFornecedor: token único (magic-link) para o fornecedor responder sem login.
- Pedido: geração do pedido ao fornecedor vencedor.
- ItemPedido: itens do pedido.
"""
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

from core.models import Categoria


class Cotacao(models.Model):
    """Cotação criada pelo cliente."""

    class Status(models.TextChoices):
        ABERTA = "aberta", "Aberta (aguardando respostas)"
        PARCIAL = "parcial", "Parcial (algumas respostas)"
        FECHADA = "fechada", "Fechada (prazo expirado)"
        CANCELADA = "cancelada", "Cancelada pelo cliente"
        PEDIDO_DISPARADO = "pedido_disparado", "Pedido(s) disparado(s)"

    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="cotacoes",
    )
    prazo_limite = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ABERTA)
    observacoes = models.TextField(blank=True, default="")
    criada_em = models.DateTimeField(auto_now_add=True)
    fechada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criada_em"]
        indexes = [
            models.Index(fields=["cliente", "status"]),
            models.Index(fields=["status", "prazo_limite"]),
        ]

    def __str__(self) -> str:
        return f"Cotação #{self.id} · {self.cliente.email} · {self.get_status_display()}"

    @property
    def total_itens(self) -> int:
        return self.itens.count()

    @property
    def itens_respondidos(self) -> int:
        return self.itens.filter(respostas_fornecedor__isnull=False).distinct().count()

    @property
    def progresso_percentual(self) -> int:
        total = self.total_itens
        if total == 0:
            return 0
        return round((self.itens_respondidos / total) * 100)


class ItemCotacao(models.Model):
    """Item individual dentro de uma cotação."""
    cotacao = models.ForeignKey(
        Cotacao,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="itens_cotacao",
    )
    produto_nome = models.CharField(max_length=200)
    quantidade = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unidade = models.CharField(max_length=20, default="un")
    descricao = models.TextField(blank=True, default="")
    ordem = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "id"]
        verbose_name = "Item da Cotação"
        verbose_name_plural = "Itens da Cotação"

    def __str__(self) -> str:
        return f"{self.produto_nome} ({self.quantidade} {self.unidade})"

    @property
    def respostas(self):
        return self.respostas_fornecedor.select_related("fornecedor").order_by("preco_unitario")

    @property
    def melhor_resposta(self):
        """Retorna a resposta de menor preço (para destaque no cliente)."""
        return self.respostas.first()


class RespostaFornecedor(models.Model):
    """Resposta de um fornecedor para um item específico."""
    item = models.ForeignKey(
        ItemCotacao,
        on_delete=models.CASCADE,
        related_name="respostas_fornecedor",
    )
    fornecedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="respostas_cotacao",
    )
    preco_unitario = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    prazo_entrega_dias = models.PositiveIntegerField(
        default=0,
        help_text="Dias úteis para entrega após confirmação",
    )
    marca = models.CharField(max_length=100, blank=True, default="")
    observacoes = models.TextField(blank=True, default="")
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["item", "fornecedor"]]
        ordering = ["preco_unitario"]
        verbose_name = "Resposta do Fornecedor"
        verbose_name_plural = "Respostas dos Fornecedores"

    def __str__(self) -> str:
        return f"{self.fornecedor.fornecedor_profile.get_display_name()} · R$ {self.preco_unitario:.2f}"

    @property
    def preco_total(self):
        return self.preco_unitario * self.item.quantidade


class CotacaoTokenFornecedor(models.Model):
    """
    Token de acesso único (magic-link) para fornecedor responder cotação sem login.
    Um token por fornecedor por cotação (agrupa itens da mesma categoria).
    """
    cotacao = models.ForeignKey(
        Cotacao,
        on_delete=models.CASCADE,
        related_name="tokens_fornecedor",
    )
    fornecedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tokens_cotacao",
    )
    token_hash = models.CharField(max_length=128, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    usado_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["cotacao", "fornecedor"]),
            models.Index(fields=["token_hash"]),
        ]

    def __str__(self) -> str:
        return f"Token #{self.id} · {self.cotacao} · {self.fornecedor.email}"

    @property
    def valido(self) -> bool:
        if self.usado_em is not None:
            return False
        # Token expira junto com a cotação (ou 7 dias, o que for menor)
        from django.conf import settings
        expira = self.criado_em + timezone.timedelta(hours=settings.TOKEN_COTACAO_VALIDADE_HORAS)
        return timezone.now() < expira and self.cotacao.status in [Cotacao.Status.ABERTA, Cotacao.Status.PARCIAL]


class Pedido(models.Model):
    """Pedido gerado ao fornecedor vencedor (após cliente confirmar)."""

    class Status(models.TextChoices):
        ENVIADO = "enviado", "Enviado ao fornecedor"
        CONFIRMADO = "confirmado", "Confirmado pelo fornecedor"
        EM_PRODUCAO = "em_producao", "Em produção"
        ENTREGUE = "entregue", "Entregue"
        CANCELADO = "cancelado", "Cancelado"

    cotacao = models.ForeignKey(
        Cotacao,
        on_delete=models.PROTECT,
        related_name="pedidos",
    )
    fornecedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pedidos_recebidos",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ENVIADO)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    observacoes = models.TextField(blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self) -> str:
        return f"Pedido #{self.id} · {self.fornecedor.fornecedor_profile.get_display_name()} · R$ {self.total:.2f}"

    def recalcular_total(self) -> None:
        self.total = sum(item.preco_total for item in self.itens.all())
        self.save(update_fields=["total"])


class ItemPedido(models.Model):
    """Item dentro de um pedido (vincula à resposta vencedora)."""
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    item_cotacao = models.ForeignKey(
        ItemCotacao,
        on_delete=models.PROTECT,
        related_name="itens_pedido",
    )
    resposta_vencedora = models.ForeignKey(
        RespostaFornecedor,
        on_delete=models.PROTECT,
        related_name="itens_pedido",
    )
    quantidade = models.PositiveIntegerField()
    preco_unitario = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        verbose_name = "Item do Pedido"
        verbose_name_plural = "Itens do Pedido"

    def __str__(self) -> str:
        return f"{self.item_cotacao.produto_nome} · R$ {self.preco_unitario:.2f}"

    @property
    def preco_total(self):
        return self.preco_unitario * self.quantidade