import pytest
from fastapi.testclient import TestClient
from app.main import app
from api.routes import autor as autor_routes
import os

os.environ["API_KEY"] = "test-api-key"

@pytest.fixture
def headers():
    return {"X-API-Key": "test-api-key"}

@pytest.fixture
def client():
    # Não precisamos abrir uma conexão real com o banco nestes testes.
    app.dependency_overrides[autor_routes.get_db] = lambda: None

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def resposta_autor():
    return {
        "autor": {
            "id": 1,
            "codigo_externo": 1,
            "nome": "Leanne Graham",
            "email": "Sincere@april.biz",
            "numero_telefone": "1-770-736-8031 x56442",
            "endereco": {
                "logradouro": "Kulas Light",
                "complemento": "Apt. 556",
                "cidade": "Gwenborough",
                "cep": "92998-3874",
            },
            "empresa": {
                "nome": "Romaguera-Crona",
                "segmento": "harness real-time e-markets",
            },
            "total_acordos": 1,
            "total_documentos": 1,
            "acordos": [
                {
                    "id": 1,
                    "codigo_externo": 1,
                    "titulo": "quidem molestiae enim",
                    "total_documentos": 1,
                    "documentos": [
                        {
                            "id": 1,
                            "codigo_externo": 1,
                            "titulo": "accusamus beatae ad facilis cum similique qui sunt",
                            "url": "https://picsum.photos/seed/1/600",
                            "url_thumbnail": "https://picsum.photos/seed/1/150",
                        }
                    ],
                }
            ],
        }
    }


def test_consultar_autor_com_acordos(client, headers, monkeypatch):
    monkeypatch.setattr(
        autor_routes,
        "consultar_acordos",
        lambda session, autor_id: resposta_autor(),
    )

    response = client.get("/api/v1/autor/1/acordos", headers=headers)

    assert response.status_code == 200

    body = response.json()["autor"]

    assert body["id"] == 1
    assert body["totalAcordos"] == 1
    assert body["totalDocumentos"] == 1
    assert len(body["acordos"]) == 1
    assert body["acordos"][0]["documentos"][0]["id"] == 1


def test_consultar_autor_inexistente(client, headers, monkeypatch):
    monkeypatch.setattr(
        autor_routes,
        "consultar_acordos",
        lambda session, autor_id: None,
    )

    response = client.get("/api/v1/autor/9999/acordos", headers=headers)

    assert response.json()["erro"]["codigo"] == 404
    assert response.json()["erro"]["mensagem"] == (
        "Autor com ID 9999 não encontrado."
    )


def test_consultar_autor_sem_acordos(client, headers, monkeypatch):
    autor_sem_acordos = resposta_autor()
    autor_sem_acordos["autor"]["total_acordos"] = 0
    autor_sem_acordos["autor"]["total_documentos"] = 0
    autor_sem_acordos["autor"]["acordos"] = []

    monkeypatch.setattr(
        autor_routes,
        "consultar_acordos",
        lambda session, autor_id: autor_sem_acordos,
    )

    response = client.get("/api/v1/autor/2/acordos", headers=headers)

    assert response.status_code == 200

    body = response.json()["autor"]

    assert body["totalAcordos"] == 0
    assert body["totalDocumentos"] == 0
    assert body["acordos"] == []

def test_consultar_sem_api_key(client):
    response = client.get("/api/v1/autor/1/acordos")

    assert response.status_code == 401
    assert response.json()["erro"]["codigo"] == 401


def test_consultar_com_api_key_invalida(client):
    response = client.get(
        "/api/v1/autor/1/acordos",
        headers={"X-API-Key": "chave-errada"},
    )

    assert response.status_code == 401
    assert response.json()["erro"]["codigo"] == 401


def test_consultar_com_id_invalido(client, headers):
    response = client.get(
        "/api/v1/autor/0/acordos",
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["erro"]["codigo"] == 400