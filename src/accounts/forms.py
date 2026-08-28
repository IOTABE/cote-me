"""
Formulários de autenticação e cadastro.
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import User, Cliente, Fornecedor


class ClienteCadastroForm(UserCreationForm):
    """Cadastro público de cliente com confirmação de e-mail."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    telefone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "(11) 99999-9999"}),
    )
    empresa = forms.CharField(
        required=False,
        label="Empresa (opcional)",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cnpj = forms.CharField(
        required=False,
        label="CNPJ (opcional)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "00.000.000/0000-00"}),
    )
    aceitou_termos = forms.BooleanField(
        required=True,
        label="Li e aceito os Termos de Uso e Política de Privacidade",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "telefone", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este e-mail já está cadastrado.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.telefone = self.cleaned_data["telefone"]
        user.aceitou_termos = True
        user.aceitou_termos_em = timezone.now()
        if commit:
            user.save()
            Cliente.objects.create(
                user=user,
                empresa=self.cleaned_data["empresa"],
                cnpj=self.cleaned_data["cnpj"],
            )
        return user


class ClienteLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )


class FornecedorLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    password = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )


class FornecedorAlterarSenhaForm(forms.Form):
    """Primeiro acesso: fornecedor troca a senha temporária."""
    senha_atual = forms.CharField(
        label="Senha atual (temporária)",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )
    nova_senha = forms.CharField(
        label="Nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    confirma_senha = forms.CharField(
        label="Confirmar nova senha",
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_nova_senha(self):
        senha = self.cleaned_data["nova_senha"]
        if len(senha) < 8:
            raise ValidationError("A senha deve ter pelo menos 8 caracteres.")
        return senha

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("nova_senha") != cleaned.get("confirma_senha"):
            raise ValidationError("As senhas não conferem.")
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["nova_senha"])
        self.user.save()


class FornecedorForm(forms.ModelForm):
    """Admin: cadastro/edição de fornecedor."""
    categorias = forms.ModelMultipleChoiceField(
        queryset=None,  # definido no __init__
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Categorias de atuação",
    )

    class Meta:
        model = Fornecedor
        fields = ("razao_social", "nome_fantasia", "cnpj", "telefone", "endereco", "ativo")
        widgets = {
            "razao_social": forms.TextInput(attrs={"class": "form-control"}),
            "nome_fantasia": forms.TextInput(attrs={"class": "form-control"}),
            "cnpj": forms.TextInput(attrs={"class": "form-control"}),
            "telefone": forms.TextInput(attrs={"class": "form-control"}),
            "endereco": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Categoria
        self.fields["categorias"].queryset = Categoria.objects.filter(ativa=True)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class FornecedorCadastroForm(UserCreationForm):
    """Cadastro público de fornecedor (pendente de aprovação do admin)."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
    )
    telefone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "(11) 99999-9999"}),
    )
    razao_social = forms.CharField(
        label="Razão social",
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    nome_fantasia = forms.CharField(
        label="Nome fantasia (opcional)",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    cnpj = forms.CharField(
        label="CNPJ",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "00.000.000/0000-00"}),
    )
    endereco = forms.CharField(
        label="Endereço (opcional)",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )
    categorias = forms.ModelMultipleChoiceField(
        queryset=None,
        required=True,
        widget=forms.CheckboxSelectMultiple,
        label="Categorias de atuação",
        help_text="Selecione as categorias de produtos que você fornece.",
    )
    aceitou_termos = forms.BooleanField(
        required=True,
        label="Li e aceito os Termos de Uso e Política de Privacidade",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "telefone", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from core.models import Categoria
        self.fields["categorias"].queryset = Categoria.objects.filter(ativa=True).order_by("nome")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este e-mail já está cadastrado.")
        return email

    def clean_cnpj(self):
        cnpj = self.cleaned_data["cnpj"]
        if Fornecedor.objects.filter(cnpj=cnpj).exists():
            raise ValidationError("Este CNPJ já está cadastrado.")
        return cnpj

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.telefone = self.cleaned_data["telefone"]
        user.aceitou_termos = True
        user.aceitou_termos_em = timezone.now()
        user.is_active = False  # aguarda confirmação de e-mail
        if commit:
            user.save()
            fornecedor = Fornecedor.objects.create(
                user=user,
                razao_social=self.cleaned_data["razao_social"],
                nome_fantasia=self.cleaned_data.get("nome_fantasia", ""),
                cnpj=self.cleaned_data["cnpj"],
                telefone=self.cleaned_data.get("telefone", ""),
                endereco=self.cleaned_data.get("endereco", ""),
                ativo=False,  # pendente de aprovação do admin
            )
            fornecedor.categorias.set(self.cleaned_data["categorias"])
        return user