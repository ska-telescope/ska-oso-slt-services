from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime, Integer, String


class Base(DeclarativeBase):
    pass


class SLT(Base):
    __tablename__ = "tab_oda_slt_images"

    id: Mapped[int] = mapped_column(Integer(), primary_key=True, nullable=False)
    slt_ref: Mapped[str] = mapped_column(String(20), nullable=False)
    image_path: Mapped[str] = mapped_column(String(20), nullable=False)
    created_by: Mapped[str] = mapped_column(String(20), nullable=False)
    created_on: Mapped[str] = mapped_column(DateTime(), nullable=False)
    last_modified_by: Mapped[str] = mapped_column(String(20), nullable=False)
    last_modified_on: Mapped[str] = mapped_column(DateTime(), nullable=False)

    def __repr__(self) -> str:
        return (
            f"tab_oda_slt_images(id={self.id!r}, "
            f"slt_ref={self.slt_ref!r}, "
            f"created_by={self.created_by!r})"
        )