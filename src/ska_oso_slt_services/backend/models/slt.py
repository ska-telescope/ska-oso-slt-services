from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Integer, String

from .metadata import Base, Metadata


class SLT(Metadata, Base):
    __tablename__ = "tab_oda_slt"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, nullable=False)
    comments: Mapped[str] = mapped_column(String(2000))

    def __repr__(self) -> str:
        return (
            f"tab_oda_slt(id={self.id!r}, "
            f"created_by={self.created_by!r}, "
            f"created_on={self.created_on!r})"
        )
