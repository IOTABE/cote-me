"""
Utilitários para geração e validação de tokens seguros (links únicos).

Formato do token:
    {token_urlsafe}.{hmac_hex}

A parte HMAC prova que o token foi emitido pelo servidor e não foi adivinhado.
A URL nunca expõe a chave.
"""
from __future__ import annotations
import hmac
import hashlib
import secrets
from typing import Tuple

from django.conf import settings


def gerar_token() -> str:
    """Gera um token aleatório seguro (sem HMAC). Usado em tokens de confirmação."""
    return secrets.token_urlsafe(32)


def assinar_token(payload: str) -> str:
    """Calcula o HMAC-SHA256 de um payload (token puro) usando TOKEN_HMAC_KEY."""
    chave = settings.TOKEN_HMAC_KEY.encode()
    return hmac.new(chave, payload.encode(), hashlib.sha256).hexdigest()


def montar_token_assinado() -> str:
    """Retorna token no formato {parte_aleatoria}.{hmac}."""
    parte_aleatoria = secrets.token_urlsafe(24)
    hmac_hex = assinar_token(parte_aleatoria)
    return f"{parte_aleatoria}.{hmac_hex}"


def validar_token_assinado(token: str) -> Tuple[bool, str | None]:
    """
    Valida o token. Retorna (valido, parte_aleatoria).
    Em caso de malformação ou HMAC inválido, retorna (False, None).
    """
    if not token or "." not in token:
        return False, None
    parte, hmac_recebido = token.rsplit(".", 1)
    hmac_esperado = assinar_token(parte)
    if not hmac.compare_digest(hmac_recebido, hmac_esperado):
        return False, None
    return True, parte
