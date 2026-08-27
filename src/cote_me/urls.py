"""
Configuração de URL raiz do projeto cote-me.
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("conta/", include("accounts.urls")),
    path("cliente/", include(("cotacoes.urls_cliente", "cliente"))),
    path("fornecedor/", include(("cotacoes.urls_fornecedor", "fornecedor"))),
    path("", include(("core.urls", "core"))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
