from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.author import Author
from app.models.agreement import Agreement


def buscar_por_id(session: Session, autor_id: int) -> Author | None:
    consulta = (
        select(Author)
        .where(Author.id == autor_id)
        .options(
            selectinload(Author.acordos)
            .selectinload(Agreement.documentos)
        )
    )

    return session.scalars(consulta).first()
