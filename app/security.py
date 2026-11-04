import os
import secrets

from fastapi import Header, HTTPException


def validar_api_key(x_api_key: str | None = Header(default=None)):
    api_key_configurada = os.getenv("API_KEY")

    if not api_key_configurada:
        raise HTTPException(
            status_code=500,
            detail="Configuração de autenticação não encontrada.",
        )

    if (
        not x_api_key
        or not secrets.compare_digest(x_api_key, api_key_configurada)
    ):
        raise HTTPException(
            status_code=401,
            detail="API Key ausente ou inválida.",
        )