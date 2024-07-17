from sqlalchemy import BIGINT, JSON, VARCHAR, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .metadata import Base, Metadata


class SLTLogs(Base, Metadata):
    __tablename__ = "tab_oda_slt_logs"

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True, autoincrement=True)
    slt_ref: Mapped[str] = mapped_column(
        BIGINT, ForeignKey(column="tab_oda_slt.id", ondelete="SET NULL")
    )
    info: Mapped[str] = mapped_column(JSON)
    source: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)

    def __repr__(self) -> str:
        return (
            f"tab_oda_slt_logs(id={self.id!r}, "
            f"slt_ref={self.slt_ref!r}, "
            f"source={self.source!r})"
        )
