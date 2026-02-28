"""Import record model – tracks CSV/PDF/XLSX file imports."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.transaction import Transaction
    from app.models.user import User


class FileType(enum.StrEnum):
    """Supported import file formats."""

    csv = "csv"
    pdf = "pdf"
    xlsx = "xlsx"


class SourceType(enum.StrEnum):
    """Import data source."""

    bank_csv = "bank_csv"
    satispay = "satispay"
    paypal = "paypal"
    pdf = "pdf"
    manual = "manual"


class ImportStatus(enum.StrEnum):
    """Import processing status."""

    pending = "pending"
    processing = "processing"
    preview = "preview"
    confirmed = "confirmed"
    failed = "failed"
    cancelled = "cancelled"


class ImportRecord(Base):
    """Record of a file import operation."""

    __tablename__ = "imports"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("accounts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(
        sa.Enum(FileType, name="file_type", native_enum=False, length=10),
        nullable=False,
    )
    source_type: Mapped[SourceType] = mapped_column(
        sa.Enum(SourceType, name="source_type", native_enum=False, length=20),
        nullable=False,
    )
    status: Mapped[ImportStatus] = mapped_column(
        sa.Enum(ImportStatus, name="import_status", native_enum=False, length=20),
        server_default="pending",
        default=ImportStatus.pending,
    )
    row_count: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("0"), default=0)
    imported_count: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("0"), default=0)
    error_log: Mapped[list[Any]] = mapped_column(
        sa.JSON, server_default=sa.text("'[]'::jsonb"), default=list
    )

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    # Relationships
    account: Mapped[Account] = relationship("Account", back_populates="imports")
    user: Mapped[User] = relationship("User", back_populates="imports")
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="import_record"
    )

    def __repr__(self) -> str:
        return f"<ImportRecord {self.filename} ({self.status.value})>"
