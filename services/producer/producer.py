
import json
import logging
import os
from uuid import uuid4

import boto3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.schemas.mensagem import (
    MensagemIngestao,
    AutorMensagem,
    AcordoMensagem,
    DocumentoMensagem,
)


API_BASE_URL = "https://jsonplaceholder.typicode.com"
HTTP_TIMEOUT = 10

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def criar_sessao_http() -> requests.Session:
    """Cria uma sessão HTTP com política de retries."""

    retry = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )

    adapter = HTTPAdapter(max_retries=retry)

    session = requests.Session()
    session.mount("https://", adapter)

    return session


def buscar_dados(
    session: requests.Session,
    endpoint: str,
) -> list[dict]:
    """Consulta um endpoint da JSONPlaceholder."""

    response = session.get(
        f"{API_BASE_URL}{endpoint}",
        timeout=HTTP_TIMEOUT,
    )

    response.raise_for_status()

    dados = response.json()

    if not isinstance(dados, list):
        raise ValueError(
            f"Resposta inesperada da API no endpoint {endpoint}"
        )

    return dados


def transformar_autor(dados: dict) -> AutorMensagem:
    endereco = dados["address"]
    empresa = dados["company"]

    return AutorMensagem(
        id_externo=dados["id"],
        nome=dados["name"],
        email=dados["email"],
        telefone=dados["phone"],
        rua=endereco["street"],
        complemento=endereco["suite"],
        cidade=endereco["city"],
        cep=endereco["zipcode"],
        nome_empresa=empresa["name"],
        segmento_empresa=empresa["bs"],
    )


def criar_mensagem(
    autor: AutorMensagem,
    acordo: dict | None,
    documentos: list[dict],
    correlation_id: str,
) -> MensagemIngestao:

    acordo_schema = (
        AcordoMensagem(
            id_externo=acordo["id"],
            titulo=acordo["title"],
        )
        if acordo
        else None
    )

    documentos_schema = [
        DocumentoMensagem(
            id_externo=documento["id"],
            titulo=documento["title"],
            url=documento["url"],
            url_miniatura=documento["thumbnailUrl"],
        )
        for documento in documentos
    ]

    return MensagemIngestao(
        message_id=str(uuid4()),
        correlation_id=correlation_id,
        autor=autor,
        acordo=acordo_schema,
        documentos=documentos_schema,
    )


def publicar_mensagem(
    sqs,
    queue_url: str,
    mensagem: MensagemIngestao,
) -> str:

    response = sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=mensagem.model_dump_json(),
    )

    return response["MessageId"]


def executar_producer():

    correlation_id = str(uuid4())

    session = criar_sessao_http()

    sqs = boto3.client(
        "sqs",
        endpoint_url=os.getenv(
            "SQS_ENDPOINT_URL",
            "http://localstack:4566",
        ),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
    )

    queue_url = sqs.get_queue_url(
        QueueName=os.getenv("SQS_QUEUE_NAME", "juridico-queue")
    )["QueueUrl"]

    total_publicadas = 0
    total_falhas = 0

    logger.info(
        "Iniciando ingestão. Correlation ID: %s",
        correlation_id,
    )

    try:
        autores = buscar_dados(session, "/users")

        for dados_autor in autores:

            autor = transformar_autor(dados_autor)

            logger.info(
                "Processando autor: %s",
                autor.id_externo,
            )

            acordos = buscar_dados(
                session,
                f"/users/{autor.id_externo}/albums",
            )

            mensagens = []

            if not acordos:
                mensagens.append(
                    criar_mensagem(
                        autor,
                        None,
                        [],
                        correlation_id,
                    )
                )

            for acordo in acordos:

                documentos = buscar_dados(
                    session,
                    f"/albums/{acordo['id']}/photos",
                )

                mensagens.append(
                    criar_mensagem(
                        autor,
                        acordo,
                        documentos,
                        correlation_id,
                    )
                )

            for mensagem in mensagens:

                try:
                    message_id = publicar_mensagem(
                        sqs,
                        queue_url,
                        mensagem,
                    )

                    total_publicadas += 1

                    logger.info(
                        "Mensagem publicada: %s",
                        message_id,
                    )

                except Exception:
                    total_falhas += 1

                    logger.exception(
                        "Falha ao publicar mensagem %s",
                        mensagem.message_id,
                    )

    except Exception:
        logger.exception(
            "Falha na ingestão. Correlation ID: %s",
            correlation_id,
        )
        raise

    finally:
        session.close()

    logger.info(
        "Ingestão finalizada. Publicadas: %d | Falhas: %d | Correlation ID: %s",
        total_publicadas,
        total_falhas,
        correlation_id,
    )

    if total_falhas:
        raise RuntimeError(
            f"{total_falhas} mensagem(ns) não foram publicadas."
        )


if __name__ == "__main__":
    executar_producer()
