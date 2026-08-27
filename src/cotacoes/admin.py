"""
Admin do app cotacoes.
"""
from django.contrib import admin
from .models import Cotacao, ItemCotacao, RespostaFornecedor, CotacaoTokenFornecedor, Pedido, ItemPedido


class ItemCotacaoInline(admin.TabularInline):
    model = ItemCotacao
    extra = 0
    readonly_fields = ()
    fields = ("categoria", "produto_nome", "quantidade", "unidade", "descricao", "ordem")


class RespostaFornecedorInline(admin.TabularInline):
    model = RespostaFornecedor
    extra = 0
    readonly_fields = ("fornecedor", "preco_unitario", "prazo_entrega_dias", "marca", "observacoes", "criada_em")
    fields = ("fornecedor", "preco_unitario", "prazo_entrega_dias", "marca", "observacoes")
    can_delete = False


class CotacaoTokenInline(admin.TabularInline):
    model = CotacaoTokenFornecedor
    extra = 0
    readonly_fields = ("fornecedor", "token_hash", "criado_em", "usado_em")
    fields = ("fornecedor", "token_hash", "criado_em", "usado_em")
    can_delete = False


@admin.register(Cotacao)
class CotacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "status", "total_itens", "itens_respondidos", "prazo_limite", "criada_em")
    list_filter = ("status", "criada_em", "prazo_limite")
    search_fields = ("id", "cliente__email", "cliente__username")
    readonly_fields = ("criada_em", "fechada_em", "total_itens", "itens_respondidos")
    inlines = [ItemCotacaoInline, CotacaoTokenInline]
    date_hierarchy = "criada_em"


@admin.register(ItemCotacao)
class ItemCotacaoAdmin(admin.ModelAdmin):
    list_display = ("id", "cotacao", "categoria", "produto_nome", "quantidade", "unidade")
    list_filter = ("categoria", "cotacao__status")
    search_fields = ("produto_nome", "cotacao__id")
    inlines = [RespostaFornecedorInline]


@admin.register(RespostaFornecedor)
class RespostaFornecedorAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "fornecedor", "preco_unitario", "prazo_entrega_dias", "criada_em")
    list_filter = ("item__categoria", "item__cotacao__status")
    search_fields = ("fornecedor__email", "item__produto_nome", "item__cotacao__id")
    readonly_fields = ("criada_em",)


@admin.register(CotacaoTokenFornecedor)
class CotacaoTokenFornecedorAdmin(admin.ModelAdmin):
    list_display = ("id", "cotacao", "fornecedor", "criado_em", "usado_em", "valido_display")
    list_filter = ("cotacao__status",)
    search_fields = ("fornecedor__email", "cotacao__id", "token_hash")
    readonly_fields = ("token_hash", "criado_em", "usado_em")

    def valido_display(self, obj):
        return "✓" if obj.valido else "✗"
    valido_display.short_description = "Válido"
    valido_display.boolean = True


class ItemPedidoInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    readonly_fields = ("item_cotacao", "resposta_vencedora", "quantidade", "preco_unitario", "preco_total")
    fields = ("item_cotacao", "resposta_vencedora", "quantidade", "preco_unitario")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "cotacao", "fornecedor", "status", "total", "criado_em")
    list_filter = ("status", "criado_em")
    search_fields = ("fornecedor__email", "cotacao__id")
    readonly_fields = ("criado_em", "atualizado_em", "total")
    inlines = [ItemPedidoInline]


@admin.register(ItemPedido)
class ItemPedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "item_cotacao", "preco_unitario", "quantidade", "preco_total")
    search_fields = ("pedido__id", "item_cotacao__produto_nome")