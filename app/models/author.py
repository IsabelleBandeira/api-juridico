from sqlalchemy import Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Author(Base):
    __tablename__ = "Autor"

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

    nome: Mapped[str] = mapped_column(
        Unicode(200),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        Unicode(254),
        nullable=False
    )

    numero_telefone: Mapped[str] = mapped_column(
        Unicode(50),
        nullable=False
    )

    logradouro: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    numero: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    cidade: Mapped[str] = mapped_column(Unicode(200), nullable=False)
    cep: Mapped[str] = mapped_column(Unicode(20), nullable=False)

    nome_empresa: Mapped[str | None] = mapped_column(
        Unicode(200),
        nullable=True
    )

    segmento_empresa: Mapped[str | None] = mapped_column(
        Unicode(200),
        nullable=True
    )

    acordos: Mapped[list["Agreement"]] = relationship(
        back_populates="Autor"
    )