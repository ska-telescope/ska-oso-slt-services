from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import BIGINT, VARCHAR

from .metadata import Base, Metadata


class SLT(Base, Metadata):
    __tablename__ = "tab_oda_slt"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    comments: Mapped[str] = mapped_column(VARCHAR(300))

    def __repr__(self) -> str:
        return (
            f"tab_oda_slt(id={self.id!r}, "
            f"created_by={self.created_by!r}, "
            f"created_on={self.created_on!r})"
        )
