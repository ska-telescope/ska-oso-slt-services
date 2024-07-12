from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import DateTime, String


class Base(DeclarativeBase):
    pass


class Metadata:

    created_by: Mapped[str] = mapped_column(String(20), nullable=False)
    created_on: Mapped[str] = mapped_column(DateTime(), nullable=False)
    last_modified_by: Mapped[str] = mapped_column(String(20), nullable=False)
    last_modified_on: Mapped[str] = mapped_column(DateTime(), nullable=False)
