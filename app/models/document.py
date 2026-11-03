from sqlalchemy import ForeignKey, Integer, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Document(Base):
    __tablename__ = "Documento"

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

    id_acordo: Mapped[int] = mapped_column(
        ForeignKey("Acordo.id"),
        nullable=False,
        index=True
    )

    titulo: Mapped[str] = mapped_column(
        Unicode(200),
        nullable=False
    )

    url: Mapped[str] = mapped_column(
        Unicode(2048),
        nullable=False
    )

    url_thumbnail: Mapped[str | None] = mapped_column(
        Unicode(2048),
        nullable=True
    )

    acordo: Mapped["Agreement"] = relationship(
        back_populates="Documento"
    )