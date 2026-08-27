"""
Formulários para criação de cotação e resposta do fornecedor.
"""
from django import forms
from django.forms import inlineformset_factory
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Cotacao, ItemCotacao, RespostaFornecedor, Pedido
from core.models import Categoria


class ItemCotacaoForm(forms.ModelForm):
    """Formulário para cada item da cotação."""

    class Meta:
        model = ItemCotacao
        fields = ("categoria", "produto_nome", "quantidade", "unidade", "descricao")
        widgets = {
            "categoria": forms.Select(attrs={"class": "form-select"}),
            "produto_nome": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Parafuso sextavado M8x50"}),
            "quantidade": forms.NumberInput(attrs={"class": "form-control", "min": "1", "value": "1"}),
            "unidade": forms.TextInput(attrs={"class": "form-control", "placeholder": "un, kg, m, cx"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Especificações, norma, observações..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categoria"].queryset = Categoria.objects.filter(ativa=True).order_by("nome")
        self.fields["categoria"].empty_label = "Selecione a categoria"


# Formset: permite adicionar vários itens na mesma cotação
ItemCotacaoFormSet = inlineformset_factory(
    Cotacao,
    ItemCotacao,
    form=ItemCotacaoForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class CotacaoForm(forms.ModelForm):
    """Formulário principal da cotação (prazo + observações)."""
    prazo_limite = forms.DateTimeField(
        label="Prazo para respostas",
        widget=forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        help_text="Mínimo 1h, máximo 30 dias a partir de agora.",
    )

    class Meta:
        model = Cotacao
        fields = ("prazo_limite", "observacoes")
        widgets = {
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Observações gerais para todos os fornecedores..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from django.conf import settings
        agora = timezone.now()
        self.fields["prazo_limite"].widget.attrs["min"] = (agora + timezone.timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")
        self.fields["prazo_limite"].widget.attrs["max"] = (agora + timezone.timedelta(days=settings.COTACAO_PRAZO_MAX_DIAS)).strftime("%Y-%m-%dT%H:%M")

    def clean_prazo_limite(self):
        from django.conf import settings
        prazo = self.cleaned_data["prazo_limite"]
        agora = timezone.now()
        if prazo < agora + timezone.timedelta(hours=1):
            raise ValidationError("O prazo deve ser de pelo menos 1 hora no futuro.")
        if prazo > agora + timezone.timedelta(days=settings.COTACAO_PRAZO_MAX_DIAS):
            raise ValidationError(f"O prazo não pode exceder {settings.COTACAO_PRAZO_MAX_DIAS} dias.")
        return prazo


class RespostaFornecedorForm(forms.ModelForm):
    """Formulário para fornecedor responder um item (via link ou dashboard)."""

    class Meta:
        model = RespostaFornecedor
        fields = ("preco_unitario", "prazo_entrega_dias", "marca", "observacoes")
        widgets = {
            "preco_unitario": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0", "placeholder": "0.00"}),
            "prazo_entrega_dias": forms.NumberInput(attrs={"class": "form-control", "min": "0", "placeholder": "0"}),
            "marca": forms.TextInput(attrs={"class": "form-control", "placeholder": "Marca do produto (opcional)"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Condições, garantia, etc."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["preco_unitario"].required = True


class RespostaFornecedorFormSet(forms.BaseModelFormSet):
    """Formset dinâmico para responder múltiplos itens de uma vez."""

    def __init__(self, *args, item_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.item_queryset = item_queryset

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if self.item_queryset and index < len(self.item_queryset):
            kwargs["instance"] = RespostaFornecedor(item=self.item_queryset[index])
        return kwargs


def get_resposta_formset(item_queryset, data=None, fornecedor=None):
    """Factory para criar formset de respostas para os itens do fornecedor."""
    # Pré-cria/instancia respostas existentes
    initial = []
    for item in item_queryset:
        resp = RespostaFornecedor.objects.filter(item=item, fornecedor=fornecedor).first()
        if resp:
            initial.append({
                "preco_unitario": resp.preco_unitario,
                "prazo_entrega_dias": resp.prazo_entrega_dias,
                "marca": resp.marca,
                "observacoes": resp.observacoes,
            })
        else:
            initial.append({})

    RespostaFormSet = forms.modelformset_factory(
        RespostaFornecedor,
        form=RespostaFornecedorForm,
        extra=0,
        can_delete=False,
    )
    return RespostaFormSet(queryset=RespostaFornecedor.objects.none(), initial=initial, data=data)


class EscolhaVencedorForm(forms.Form):
    """Formulário para cliente escolher o vencedor de cada item (após cotação fechada)."""
    def __init__(self, *args, item_cotacao=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.item = item_cotacao
        if item_cotacao:
            respostas = item_cotacao.respostas
            choices = [(r.id, f"{r.fornecedor.fornecedor_profile.get_display_name()} — R$ {r.preco_unitario:.2f} ({r.prazo_entrega_dias} dias)") for r in respostas]
            # Marca o menor preço como inicial
            melhor = item_cotacao.melhor_resposta
            initial = melhor.id if melhor else None
            self.fields["vencedor"] = forms.ChoiceField(
                label=f"Vencedor para {item_cotacao.produto_nome}",
                choices=choices,
                initial=initial,
                widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
                help_text="Opção em destaque = menor preço",
            )


class PedidoForm(forms.ModelForm):
    """Formulário para confirmação de pedido (apenas observações do cliente)."""

    class Meta:
        model = Pedido
        fields = ("observacoes",)
        widgets = {
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Instruções para o fornecedor..."}),
        }