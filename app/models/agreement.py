from sqlalchemy import ForeignKey, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Agreement(Base):
    __tablename__ = "Acordo"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    codigo_externo: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True
    )

    id_autor: Mapped[int] = mapped_column(
        ForeignKey("Autor.id"),
        nullable=False,
        index=True
    )

    titulo: Mapped[str] = mapped_column(
        Unicode(200),
        nullable=False
    )

    autor: Mapped["Author"] = relationship(
        back_populates="Acordo"
    )

    documentos: Mapped[list["Document"]] = relationship(
        back_populates="Acordo"
    )