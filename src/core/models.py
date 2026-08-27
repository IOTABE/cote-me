"""
Modelo de Categoria de produtos.
Gerenciado exclusivamente pelo admin.
"""
from django.db import models
from django.urls import reverse


class Categoria(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    descricao = models.TextField(blank=True, default="")
    ativa = models.BooleanField(default=True)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self) -> str:
        return self.nome

    def get_absolute_url(self) -> str:
        return reverse("core:categoria_detalhe", args=[self.slug])
