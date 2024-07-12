from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Integer, String

from .metadata import Base, Metadata


class SLT(Metadata, Base):
    __tablename__ = "tab_oda_slt_images"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, nullable=False)
    slt_ref: Mapped[str] = mapped_column(String(20), nullable=False)
    image_path: Mapped[str] = mapped_column(String(20), nullable=False)

    def __repr__(self) -> str:
        return (
            f"tab_oda_slt_images(id={self.id!r}, "
            f"slt_ref={self.slt_ref!r}, "
            f"created_by={self.created_by!r})"
        )
