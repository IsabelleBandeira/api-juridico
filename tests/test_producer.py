
import json
from unittest.mock import MagicMock

import pytest
import requests
from urllib3.util.retry import Retry

from services.producer import producer
from app.schemas.mensagem import MensagemIngestao
from app.schemas.mensagem import AutorMensagem


# ---------------------------------------------------------------------
# Dados de exemplo
# ---------------------------------------------------------------------

AUTOR_API = {
    "id": 1,
    "name": "Leanne Graham",
    "username": "Bret",
    "email": "Sincere@april.biz",
    "address": {
        "street": "Kulas Light",
        "suite": "Apt. 556",
        "city": "Gwenborough",
        "zipcode": "92998-3874",
    },
    "phone": "1-770-736-8031 x56442",
    "website": "hildegard.org",
    "company": {
        "name": "Romaguera-Crona",
        "catchPhrase": "Multi-layered client-server neural-net",
        "bs": "harness real-time e-markets",
    },
}

ACORDO_API = {
    "userId": 1,
    "id": 1,
    "title": "quidem molestiae enim",
}

DOCUMENTO_API = {
    "albumId": 1,
    "id": 1,
    "title": "accusamus beatae ad facilis cum similique qui sunt",
    "url": "https://via.placeholder.com/600/92c952",
    "thumbnailUrl": "https://via.placeholder.com/150/92c952",
}


@pytest.fixture
def sessao_mock():
    return MagicMock()


@pytest.fixture
def sqs_mock():
    sqs = MagicMock()
    sqs.get_queue_url.return_value = {
        "QueueUrl": "http://localstack:4566/000000000000/juridico-queue"
    }
    sqs.send_message.return_value = {"MessageId": "sqs-message-123"}
    return sqs


# ---------------------------------------------------------------------
# 1. Sessão HTTP e busca de dados
# ---------------------------------------------------------------------

def test_criar_sessao_http_configura_retries():
    session = producer.criar_sessao_http()

    adapter = session.get_adapter("https://jsonplaceholder.typicode.com")

    assert isinstance(adapter.max_retries, Retry)
    assert adapter.max_retries.total == 3
    assert adapter.max_retries.backoff_factor == 0.5
    assert set(adapter.max_retries.status_forcelist) == {
        429, 500, 502, 503, 504
    }
    assert adapter.max_retries.allowed_methods == ["GET"]

    session.close()


def test_buscar_dados_retorna_lista(sessao_mock):
    response = MagicMock()
    response.json.return_value = [AUTOR_API]
    sessao_mock.get.return_value = response

    resultado = producer.buscar_dados(sessao_mock, "/users")

    assert resultado == [AUTOR_API]
    sessao_mock.get.assert_called_once_with(
        f"{producer.API_BASE_URL}/users",
        timeout=producer.HTTP_TIMEOUT,
    )
    response.raise_for_status.assert_called_once()


def test_buscar_dados_rejeita_resposta_que_nao_seja_lista(sessao_mock):
    response = MagicMock()
    response.json.return_value = {"id": 1}
    sessao_mock.get.return_value = response

    with pytest.raises(ValueError, match="Resposta inesperada"):
        producer.buscar_dados(sessao_mock, "/users")


def test_buscar_dados_propaga_erro_http(sessao_mock):
    sessao_mock.get.side_effect = requests.exceptions.HTTPError(
        "Erro HTTP"
    )

    with pytest.raises(requests.exceptions.HTTPError):
        producer.buscar_dados(sessao_mock, "/users")


# ---------------------------------------------------------------------
# 2. Transformação e criação de mensagens
# ---------------------------------------------------------------------

def test_transformar_autor_converte_campos():
    autor = producer.transformar_autor(AUTOR_API)

    assert autor.id_externo == 1
    assert autor.nome == "Leanne Graham"
    assert autor.email == "Sincere@april.biz"
    assert autor.telefone == "1-770-736-8031 x56442"
    assert autor.rua == "Kulas Light"
    assert autor.complemento == "Apt. 556"
    assert autor.cidade == "Gwenborough"
    assert autor.cep == "92998-3874"
    assert autor.nome_empresa == "Romaguera-Crona"
    assert autor.segmento_empresa == "harness real-time e-markets"


def test_criar_mensagem_com_acordo_e_documentos():
    autor = producer.transformar_autor(AUTOR_API)

    mensagem = producer.criar_mensagem(
        autor=autor,
        acordo=ACORDO_API,
        documentos=[DOCUMENTO_API],
        correlation_id="correlation-123",
    )

    assert isinstance(mensagem, MensagemIngestao)
    assert mensagem.message_id
    assert mensagem.correlation_id == "correlation-123"

    assert mensagem.autor.id_externo == 1

    assert mensagem.acordo is not None
    assert mensagem.acordo.id_externo == 1
    assert mensagem.acordo.titulo == "quidem molestiae enim"

    assert len(mensagem.documentos) == 1
    assert mensagem.documentos[0].id_externo == 1
    assert mensagem.documentos[0].titulo == DOCUMENTO_API["title"]
    assert mensagem.documentos[0].url == DOCUMENTO_API["url"]
    assert (
        mensagem.documentos[0].url_miniatura
        == DOCUMENTO_API["thumbnailUrl"]
    )


def test_criar_mensagem_sem_acordo_e_sem_documentos():
    autor = producer.transformar_autor(AUTOR_API)

    mensagem = producer.criar_mensagem(
        autor=autor,
        acordo=None,
        documentos=[],
        correlation_id="correlation-123",
    )

    assert mensagem.acordo is None
    assert mensagem.documentos == []
    assert mensagem.autor.id_externo == 1
    assert mensagem.correlation_id == "correlation-123"


# ---------------------------------------------------------------------
# 3. Publicação na SQS
# ---------------------------------------------------------------------

def test_publicar_mensagem_envia_json_para_sqs(sqs_mock):
    autor = producer.transformar_autor(AUTOR_API)

    mensagem = producer.criar_mensagem(
        autor=autor,
        acordo=ACORDO_API,
        documentos=[DOCUMENTO_API],
        correlation_id="correlation-123",
    )

    resultado = producer.publicar_mensagem(
        sqs=sqs_mock,
        queue_url="queue-url",
        mensagem=mensagem,
    )

    assert resultado == "sqs-message-123"

    sqs_mock.send_message.assert_called_once()
    chamada = sqs_mock.send_message.call_args.kwargs

    assert chamada["QueueUrl"] == "queue-url"

    payload = json.loads(chamada["MessageBody"])

    assert payload["message_id"] == mensagem.message_id
    assert payload["correlation_id"] == "correlation-123"
    assert payload["autor"]["id_externo"] == 1
    assert payload["acordo"]["id_externo"] == 1
    assert len(payload["documentos"]) == 1


def test_publicar_mensagem_propaga_falha_sqs(sqs_mock):
    autor = producer.transformar_autor(AUTOR_API)

    mensagem = producer.criar_mensagem(
        autor=autor,
        acordo=ACORDO_API,
        documentos=[],
        correlation_id="correlation-123",
    )

    sqs_mock.send_message.side_effect = RuntimeError("Erro na SQS")

    with pytest.raises(RuntimeError, match="Erro na SQS"):
        producer.publicar_mensagem(
            sqs=sqs_mock,
            queue_url="queue-url",
            mensagem=mensagem,
        )


# ---------------------------------------------------------------------
# 4. Orquestração do Producer
# ---------------------------------------------------------------------

def configurar_producer_mock(monkeypatch, sessao, sqs):
    monkeypatch.setattr(
        producer,
        "criar_sessao_http",
        lambda: sessao,
    )

    monkeypatch.setattr(
        producer.boto3,
        "client",
        lambda *args, **kwargs: sqs,
    )


def test_executar_producer_publica_mensagens(monkeypatch):
    sessao = MagicMock()
    sqs = MagicMock()
    sqs.get_queue_url.return_value = {"QueueUrl": "queue-url"}

    configurar_producer_mock(monkeypatch, sessao, sqs)

    def buscar_dados_mock(session, endpoint):
        if endpoint == "/users":
            return [AUTOR_API]
        if endpoint == "/users/1/albums":
            return [ACORDO_API]
        if endpoint == "/albums/1/photos":
            return [DOCUMENTO_API]
        raise AssertionError(f"Endpoint inesperado: {endpoint}")

    monkeypatch.setattr(
        producer,
        "buscar_dados",
        buscar_dados_mock,
    )

    mensagens_publicadas = []

    def publicar_mock(sqs_client, queue_url, mensagem):
        mensagens_publicadas.append(mensagem)
        return f"sqs-{mensagem.message_id}"

    monkeypatch.setattr(
        producer,
        "publicar_mensagem",
        publicar_mock,
    )

    producer.executar_producer()

    assert len(mensagens_publicadas) == 1
    assert mensagens_publicadas[0].autor.id_externo == 1
    assert mensagens_publicadas[0].acordo.id_externo == 1
    assert len(mensagens_publicadas[0].documentos) == 1

    sqs.get_queue_url.assert_called_once_with(
        QueueName="juridico-queue"
    )
    sessao.close.assert_called_once()


def test_executar_producer_cria_mensagem_quando_autor_nao_tem_acordos(
    monkeypatch,
):
    sessao = MagicMock()
    sqs = MagicMock()
    sqs.get_queue_url.return_value = {"QueueUrl": "queue-url"}

    configurar_producer_mock(monkeypatch, sessao, sqs)

    def buscar_dados_mock(session, endpoint):
        if endpoint == "/users":
            return [AUTOR_API]
        if endpoint == "/users/1/albums":
            return []
        raise AssertionError(f"Endpoint inesperado: {endpoint}")

    monkeypatch.setattr(
        producer,
        "buscar_dados",
        buscar_dados_mock,
    )

    mensagens_publicadas = []

    def publicar_mock(sqs_client, queue_url, mensagem):
        mensagens_publicadas.append(mensagem)
        return "sqs-message-123"

    monkeypatch.setattr(
        producer,
        "publicar_mensagem",
        publicar_mock,
    )

    producer.executar_producer()

    assert len(mensagens_publicadas) == 1
    assert mensagens_publicadas[0].acordo is None
    assert mensagens_publicadas[0].documentos == []
    sessao.close.assert_called_once()


def test_executar_producer_propaga_falha_http_e_fecha_sessao(
    monkeypatch,
):
    sessao = MagicMock()
    sqs = MagicMock()
    sqs.get_queue_url.return_value = {"QueueUrl": "queue-url"}

    configurar_producer_mock(monkeypatch, sessao, sqs)

    monkeypatch.setattr(
        producer,
        "buscar_dados",
        MagicMock(
            side_effect=requests.exceptions.ConnectionError(
                "API indisponível"
            )
        ),
    )

    with pytest.raises(requests.exceptions.ConnectionError):
        producer.executar_producer()

    sessao.close.assert_called_once()


def test_executar_producer_registra_falha_de_publicacao_e_lanca_erro(
    monkeypatch,
):
    sessao = MagicMock()
    sqs = MagicMock()
    sqs.get_queue_url.return_value = {"QueueUrl": "queue-url"}

    configurar_producer_mock(monkeypatch, sessao, sqs)

    def buscar_dados_mock(session, endpoint):
        if endpoint == "/users":
            return [AUTOR_API]
        if endpoint == "/users/1/albums":
            return [ACORDO_API]
        if endpoint == "/albums/1/photos":
            return [DOCUMENTO_API]
        raise AssertionError(f"Endpoint inesperado: {endpoint}")

    monkeypatch.setattr(
        producer,
        "buscar_dados",
        buscar_dados_mock,
    )

    monkeypatch.setattr(
        producer,
        "publicar_mensagem",
        MagicMock(side_effect=RuntimeError("SQS indisponível")),
    )

    with pytest.raises(RuntimeError, match="1 mensagem"):
        producer.executar_producer()

    sessao.close.assert_called_once()

def test_autor_mensagem_aceita_complemento_nulo():
    autor = AutorMensagem(
        id_externo=1,
        nome="Leanne Graham",
        email="leanne@example.com",
        telefone="1-770-736-8031",
        rua="Kulas Light",
        complemento=None,
        cidade="Gwenborough",
        cep="92998-3874",
        nome_empresa="Romaguera-Crona",
        segmento_empresa="Multi-layered client-server neural-net",
    )

    assert autor.complemento is None


def test_transformar_autor_aceita_complemento_nulo():
    dados_autor = {
        "id": 1,
        "name": "Leanne Graham",
        "email": "leanne@example.com",
        "phone": "1-770-736-8031",
        "address": {
            "street": "Kulas Light",
            "suite": None,
            "city": "Gwenborough",
            "zipcode": "92998-3874",
        },
        "company": {
            "name": "Romaguera-Crona",
            "bs": "Multi-layered client-server neural-net",
        },
    }

    autor = producer.transformar_autor(dados_autor)

    assert autor.complemento is None
