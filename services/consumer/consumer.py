import json
import logging
import os

import boto3
from botocore.exceptions import ClientError
from sqlalchemy import select

from app.database import SessionLocal
from app.models.author import Author
from app.models.agreement import Agreement
from app.models.document import Document
from app.schemas.mensagem import MensagemIngestao
from app.logging_config import configurar_logs

configurar_logs()
logger = logging.getLogger(__name__)


# Configurações SQS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "juridico-queue")
LOCALSTACK_ENDPOINT = os.getenv(
    "LOCALSTACK_ENDPOINT",
    "http://localstack:4566",
)

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    endpoint_url=LOCALSTACK_ENDPOINT,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
)

queue_url = sqs.get_queue_url(
    QueueName=QUEUE_NAME
)["QueueUrl"]


def salvar_mensagem(dados: MensagemIngestao):
    """
    Persiste autor, acordo e documentos em uma única transação.
    Se qualquer operação falhar, todas as alterações dessa
    mensagem serão revertidas.
    """

    if dados.acordo is None and dados.documentos:
        raise ValueError(
            "Uma mensagem sem acordo não pode possuir documentos."
        )

    with SessionLocal() as session:
        with session.begin():

            # 1. Localiza ou cria o autor
            autor = session.scalar(
                select(Author).where(
                    Author.codigo_externo == dados.autor.id_externo
                )
            )

            if autor is None:
                autor = Author(
                    codigo_externo=dados.autor.id_externo,
                )
                session.add(autor)

            # Atualiza os dados do autor
            autor.nome = dados.autor.nome
            autor.email = dados.autor.email
            autor.numero_telefone = dados.autor.telefone
            autor.logradouro = dados.autor.rua
            autor.complemento = dados.autor.complemento
            autor.cidade = dados.autor.cidade
            autor.cep = dados.autor.cep
            autor.nome_empresa = dados.autor.nome_empresa
            autor.segmento_empresa = dados.autor.segmento_empresa

            # Garante que o ID interno esteja disponível
            session.flush()

            if dados.acordo is None:
                return

            # 2. Localiza ou cria o acordo
            acordo = session.scalar(
                select(Agreement).where(
                    Agreement.codigo_externo
                    == dados.acordo.id_externo
                )
            )

            if acordo is None:
                acordo = Agreement(
                    codigo_externo=dados.acordo.id_externo,
                    id_autor=autor.id,
                    titulo=dados.acordo.titulo,
                )
                session.add(acordo)
            else:
                acordo.id_autor = autor.id
                acordo.titulo = dados.acordo.titulo

            session.flush()

            # 3. Localiza ou cria os documentos
            for documento_dados in dados.documentos:

                documento = session.scalar(
                    select(Document).where(
                        Document.codigo_externo
                        == documento_dados.id_externo
                    )
                )

                if documento is None:
                    documento = Document(
                        codigo_externo=documento_dados.id_externo,
                        id_acordo=acordo.id,
                        titulo=documento_dados.titulo,
                        url=documento_dados.url,
                        url_thumbnail=documento_dados.url_miniatura,
                    )
                    session.add(documento)
                else:
                    documento.id_acordo = acordo.id
                    documento.titulo = documento_dados.titulo
                    documento.url = documento_dados.url
                    documento.url_thumbnail = (
                        documento_dados.url_miniatura
                    )

            session.flush()

    # Ao sair de session.begin(), a transação já foi confirmada.


def processar_mensagem(mensagem_sqs: dict):
    """
    Processa uma mensagem individual.
    Lança exceção se houver falha, permitindo retry pelo SQS.
    """

    corpo = json.loads(mensagem_sqs["Body"])
    dados = MensagemIngestao.model_validate(corpo)

    salvar_mensagem(dados)

    logger.info(
        "Mensagem Processada com Sucesso | "
        "app_message_id=%s sqs_message_id=%s correlation_id=%s",
        dados.message_id,
        mensagem_sqs.get("MessageId"),
        dados.correlation_id,
    )


def processar_lote(mensagens: list[dict]):
    processadas = 0
    falhas = 0

    for mensagem in mensagens:
        sqs_message_id = mensagem.get("MessageId")

        try:
            processar_mensagem(mensagem)

        except Exception:
            falhas += 1

            logger.exception(
                "Falha no Processamento da Mensagem | sqs_message_id=%s",
                sqs_message_id,
            )
            continue

        try:
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=mensagem["ReceiptHandle"],
            )

            processadas += 1

            logger.info(
                "Mensagem Deletada | sqs_message_id=%s",
                sqs_message_id,
            )

        except Exception:
            falhas += 1

            logger.exception(
                "Falha ao Excluir a Mensagem | sqs_message_id=%s",
                sqs_message_id,
            )

    logger.info(
        "Lote Finalizado | processadas=%d falhas=%d",
        processadas,
        falhas,
    )


def executar_consumer():
    logger.info("Consumer iniciado. Aguardando mensagens...")

    while True:
        try:
            resposta = sqs.receive_message(
                QueueUrl=queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=20,
                VisibilityTimeout=60,
            )

            mensagens = resposta.get("Messages", [])

            if not mensagens:
                continue

            logger.info(
                "Recebido lote com %s mensagens.",
                len(mensagens),
            )

            processar_lote(mensagens)

        except ClientError:
            logger.exception("Erro de comunicação com SQS.")

        except Exception:
            logger.exception("Erro inesperado no Consumer.")


if __name__ == "__main__":
    executar_consumer()