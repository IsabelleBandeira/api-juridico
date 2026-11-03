from pydantic import ValidationError
import pytest

from app.schemas.mensagem import MensagemIngestao


def mensagem_base():
    return {
        "message_id": "msg-001",
        "correlation_id": "ingestao-001",
        "autor": {
            "id_externo": 1,
            "nome": "Leanne Graham",
            "email": "leanne@example.com",
            "telefone": "1-770-736-8031",
            "rua": "Kulas Light",
            "complemento": "Apt. 556",
            "cidade": "Gwenborough",
            "cep": "92998-387",
            "nome_empresa": "Romaguera-Crona",
            "segmento_empresa": "Multi-layered client-server neural-net",
        },
        "acordo": None,
        "documentos": [],
    }


def test_mensagem_autor_sem_acordo():
    mensagem = MensagemIngestao.model_validate(mensagem_base())

    assert mensagem.autor.id_externo == 1
    assert mensagem.acordo is None
    assert mensagem.documentos == []


def test_mensagem_com_acordo_e_documento():
    dados = mensagem_base()
    dados["acordo"] = {
        "id_externo": 10,
        "titulo": "Acordo de exemplo",
    }
    dados["documentos"] = [
        {
            "id_externo": 100,
            "titulo": "Documento de exemplo",
            "url": "https://example.com/documento",
            "url_miniatura": "https://example.com/thumbnail",
        }
    ]

    mensagem = MensagemIngestao.model_validate(dados)

    assert mensagem.acordo.id_externo == 10
    assert len(mensagem.documentos) == 1


def test_mensagem_sem_autor_e_invalida():
    dados = mensagem_base()
    del dados["autor"]

    with pytest.raises(ValidationError):
        MensagemIngestao.model_validate(dados)