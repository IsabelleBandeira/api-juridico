from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.usuario import UsuarioResposta
from services.query.usuario_service import consultar_acordos
from app.security import validar_api_key

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
    resultado = consultar_acordos(session, autor_id)

    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"Autor com ID {autor_id} não encontrado.",
        )

    return resultado