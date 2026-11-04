from sqlalchemy.orm import Session

from app.repositories.usuario_repository import buscar_por_id
from app.schemas.usuario import (
    UsuarioResposta,
    AutorResposta,
    EnderecoResposta,
    EmpresaResposta,
    AcordoResposta,
    DocumentoResposta,
)


def consultar_acordos(session: Session, autor_id: int) -> UsuarioResposta | None:
    autor = buscar_por_id(session, autor_id)

    if autor is None:
        return None

    acordos = []
    total_documentos = 0

    for acordo in autor.acordos:
        documentos = [
            DocumentoResposta.model_validate(documento)
            for documento in acordo.documentos
        ]

        quantidade_documentos = len(documentos)
        total_documentos += quantidade_documentos

        acordos.append(
            AcordoResposta(
                id=acordo.id,
                codigo_externo=acordo.codigo_externo,
                titulo=acordo.titulo,
                total_documentos=quantidade_documentos,
                documentos=documentos,
            )
        )

    resposta = AutorResposta(
        id=autor.id,
        codigo_externo=autor.codigo_externo,
        nome=autor.nome,
        email=autor.email,
        numero_telefone=autor.numero_telefone,
        endereco=EnderecoResposta(
            logradouro=autor.logradouro,
            complemento=autor.complemento,
            cidade=autor.cidade,
            cep=autor.cep,
        ),
        empresa=EmpresaResposta(
            nome=autor.nome_empresa,
            segmento=autor.segmento_empresa,
        ),
        total_acordos=len(acordos),
        total_documentos=total_documentos,
        acordos=acordos,
    )

    return UsuarioResposta(autor=resposta)
