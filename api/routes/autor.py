from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from app.database import SessionLocal
from app.schemas.usuario import UsuarioResposta
from services.query.usuario_service import consultar_acordos
from app.security import validar_api_key
from app.logging_config import configurar_logs
import logging

configurar_logs()
logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/autor", tags=["Autores"])


def get_db():
    with SessionLocal() as session:
        yield session


@router.get(
    "/{autor_id}/acordos",
    response_model=UsuarioResposta,
    dependencies=[Depends(validar_api_key)],
)
def consultar_acordos_autor(
    autor_id: int = Path(gt=0),
    session: Session = Depends(get_db),
):
    try:
        resultado = consultar_acordos(session, autor_id)
    except HTTPException:
        raise
    except OperationalError:
        raise HTTPException(
            status_code=503,
            detail="Serviço temporariamente indisponível."
        )
    except Exception:
        logger.exception("Erro inesperado ao consultar acordos do autor %s", autor_id)
        raise HTTPException(
            status_code=500,
            detail=f"Algo deu errado ao consultar os dados."
        )

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"Autor com ID {autor_id} não encontrado.",
        )

    return resultado
