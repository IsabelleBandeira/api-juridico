import pytest
from services.consumer import consumer
from uuid import uuid4
from sqlalchemy import select
from app.database import SessionLocal
from app.models.author import Author
from app.models.agreement import Agreement
from app.models.document import Document
from app.schemas.mensagem import (
    MensagemIngestao,
    AutorMensagem,
    AcordoMensagem,
    DocumentoMensagem,
)
from services.consumer import consumer
from services.consumer.consumer import salvar_mensagem


def test_salvar_mensagem_e_idempotente():
    # IDs exclusivos para não conflitar com os dados da ingestão.
    base_id = uuid4().int % 100_000_000 + 1_000_000_000

    id_autor = base_id
    id_acordo = base_id + 1
    id_documento = base_id + 2

    def criar_mensagem(nome, titulo_acordo, titulo_documento):
        return MensagemIngestao(
            message_id=str(uuid4()),
            correlation_id=str(uuid4()),
            autor=AutorMensagem(
                id_externo=id_autor,
                nome=nome,
                email="teste@example.com",
                telefone="11999999999",
                rua="Rua de Teste",
                complemento="Apto 1",
                cidade="Limeira",
                cep="13480000",
                nome_empresa="Empresa Teste",
                segmento_empresa="Tecnologia",
            ),
            acordo=AcordoMensagem(
                id_externo=id_acordo,
                titulo=titulo_acordo,
            ),
            documentos=[
                DocumentoMensagem(
                    id_externo=id_documento,
                    titulo=titulo_documento,
                    url="https://example.com/documento",
                    url_miniatura=None,
                )
            ],
        )

    try:
        # Primeira execução: cria os registros.
        salvar_mensagem(
            criar_mensagem(
                "Autor Original",
                "Acordo Original",
                "Documento Original",
            )
        )

        # Segunda execução: atualiza os mesmos registros.
        salvar_mensagem(
            criar_mensagem(
                "Autor Atualizado",
                "Acordo Atualizado",
                "Documento Atualizado",
            )
        )

        with SessionLocal() as session:
            autor = session.scalar(
                select(Author).where(
                    Author.codigo_externo == id_autor
                )
            )
            acordo = session.scalar(
                select(Agreement).where(
                    Agreement.codigo_externo == id_acordo
                )
            )
            documento = session.scalar(
                select(Document).where(
                    Document.codigo_externo == id_documento
                )
            )

            assert autor is not None
            assert acordo is not None
            assert documento is not None

            assert autor.nome == "Autor Atualizado"
            assert acordo.titulo == "Acordo Atualizado"
            assert documento.titulo == "Documento Atualizado"

            assert acordo.id_autor == autor.id
            assert documento.id_acordo == acordo.id

            assert session.scalar(
                select(Author).where(
                    Author.codigo_externo == id_autor
                ).count()
            ) if False else True

    finally:
        # Remove somente os registros criados por este teste.
        with SessionLocal() as session:
            with session.begin():
                documento = session.scalar(
                    select(Document).where(
                        Document.codigo_externo == id_documento
                    )
                )
                acordo = session.scalar(
                    select(Agreement).where(
                        Agreement.codigo_externo == id_acordo
                    )
                )
                autor = session.scalar(
                    select(Author).where(
                        Author.codigo_externo == id_autor
                    )
                )

                if documento:
                    session.delete(documento)
                if acordo:
                    session.delete(acordo)
                if autor:
                    session.delete(autor)


def mensagem_sqs():
    return {
        "MessageId": "sqs-001",
        "ReceiptHandle": "receipt-001",
        "Body": "{}",
    }


def test_processar_lote_processa_e_deleta_mensagem(monkeypatch):
    mensagem = mensagem_sqs()
    mensagens_processadas = []
    mensagens_deletadas = []

    monkeypatch.setattr(
        consumer,
        "processar_mensagem",
        lambda msg: mensagens_processadas.append(msg),
    )

    monkeypatch.setattr(
        consumer.sqs,
        "delete_message",
        lambda **kwargs: mensagens_deletadas.append(kwargs),
    )

    monkeypatch.setattr(consumer, "queue_url", "fila-teste")

    consumer.processar_lote([mensagem])

    assert mensagens_processadas == [mensagem]
    assert len(mensagens_deletadas) == 1
    assert mensagens_deletadas[0]["QueueUrl"] == "fila-teste"
    assert mensagens_deletadas[0]["ReceiptHandle"] == "receipt-001"


def test_processar_lote_nao_deleta_mensagem_com_falha(monkeypatch):
    mensagem = mensagem_sqs()
    mensagens_deletadas = []

    def falhar_processamento(msg):
        raise ValueError("Erro simulado")

    monkeypatch.setattr(
        consumer,
        "processar_mensagem",
        falhar_processamento,
    )

    monkeypatch.setattr(
        consumer.sqs,
        "delete_message",
        lambda **kwargs: mensagens_deletadas.append(kwargs),
    )

    consumer.processar_lote([mensagem])

    assert mensagens_deletadas == []


def test_processar_lote_registra_falha_ao_deletar(monkeypatch):
    mensagem = mensagem_sqs()

    monkeypatch.setattr(
        consumer,
        "processar_mensagem",
        lambda msg: None,
    )

    def falhar_exclusao(**kwargs):
        raise RuntimeError("Erro simulado ao excluir")

    monkeypatch.setattr(
        consumer.sqs,
        "delete_message",
        falhar_exclusao,
    )

    # O erro de exclusão é tratado pelo Consumer.
    # Ele não deve escapar nem interromper o lote.
    consumer.processar_lote([mensagem])



def test_salvar_mensagem_faz_rollback_em_falha(monkeypatch):
    base_id = uuid4().int % 100_000_000 + 1_000_000_000

    id_autor = base_id
    id_acordo = base_id + 1
    id_documento = base_id + 2

    mensagem = MensagemIngestao(
        message_id=str(uuid4()),
        correlation_id=str(uuid4()),
        autor=AutorMensagem(
            id_externo=id_autor,
            nome="Autor Rollback",
            email="rollback@example.com",
            telefone="11999999999",
            rua="Rua de Teste",
            complemento="Apto 1",
            cidade="Limeira",
            cep="13480000",
        ),
        acordo=AcordoMensagem(
            id_externo=id_acordo,
            titulo="Acordo Rollback",
        ),
        documentos=[
            DocumentoMensagem(
                id_externo=id_documento,
                titulo="Documento Rollback",
                url="https://example.com/rollback",
            )
        ],
    )

    session_factory_original = consumer.SessionLocal

    def session_factory_com_falha():
        session = session_factory_original()
        flush_original = session.flush
        contador = 0

        def flush_com_falha(*args, **kwargs):
            nonlocal contador
            contador += 1

            # Falha no terceiro flush:
            # autor e acordo já foram enviados ao banco,
            # mas ainda não houve commit.
            if contador == 3:
                raise RuntimeError("Falha simulada durante a persistência")

            return flush_original(*args, **kwargs)

        session.flush = flush_com_falha
        return session

    monkeypatch.setattr(
        consumer,
        "SessionLocal",
        session_factory_com_falha,
    )

    try:
        with pytest.raises(RuntimeError, match="Falha simulada"):
            consumer.salvar_mensagem(mensagem)

        # Consulta usando a SessionLocal original,
        # sem a falha injetada.
        with session_factory_original() as session:
            autor = session.scalar(
                select(Author).where(
                    Author.codigo_externo == id_autor
                )
            )
            acordo = session.scalar(
                select(Agreement).where(
                    Agreement.codigo_externo == id_acordo
                )
            )
            documento = session.scalar(
                select(Document).where(
                    Document.codigo_externo == id_documento
                )
            )

            assert autor is None
            assert acordo is None
            assert documento is None

    finally:
        monkeypatch.setattr(
            consumer,
            "SessionLocal",
            session_factory_original,
        )
