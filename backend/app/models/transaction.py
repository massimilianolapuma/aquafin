"""Transaction model."""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TransactionType(str, enum.Enum):
    """Transaction direction."""

    income = "income"
    expense = "expense"
    transfer = "transfer"


class CategorizationMethod(str, enum.Enum):
    """How the transaction was categorized."""

    manual = "manual"
    rule = "rule"
    keyword = "keyword"
    pattern = "pattern"
    ai = "ai"
    uncategorized = "uncategorized"


class Transaction(Base):
    """Single financial transaction."""

    __tablename__ = "transactions"
    __table_args__ = (
        sa.Index("ix_transactions_account_date", "account_id", "date"),
        sa.Index("ix_transactions_category_id", "category_id"),
    )

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
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    import_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("imports.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[Decimal] = mapped_column(
        sa.Numeric(12, 2), nullable=False
    )
    currency: Mapped[str] = mapped_column(
        sa.String(3), server_default="EUR", default="EUR"
    )
    date: Mapped[date] = mapped_column(
        sa.Date, nullable=False, index=True
    )
    description: Mapped[str | None] = mapped_column(sa.String(500), nullable=True)
    original_description: Mapped[str | None] = mapped_column(
        sa.String(500), nullable=True
    )
    type: Mapped[TransactionType] = mapped_column(
        sa.Enum(TransactionType, name="transaction_type", native_enum=False, length=20),
        nullable=False,
    )
    categorization_method: Mapped[CategorizationMethod | None] = mapped_column(
        sa.Enum(
            CategorizationMethod,
            name="categorization_method",
            native_enum=False,
            length=20,
        ),
        nullable=True,
    )
    is_recurring: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.text("false"), default=False
    )
    tags: Mapped[list[str]] = mapped_column(
        sa.ARRAY(sa.String), server_default=sa.text("'{}'::text[]"), default=list
    )
    metadata_extra: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, server_default=sa.text("'{}'::jsonb"), default=dict
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
    account: Mapped[Account] = relationship("Account", back_populates="transactions")
    category: Mapped[Category | None] = relationship(
        "Category", back_populates="transactions"
    )
    import_record: Mapped[ImportRecord | None] = relationship(
        "ImportRecord", back_populates="transactions"
    )

    def __repr__(self) -> str:
        return f"<Transaction {self.amount} {self.currency} on {self.date}>"
