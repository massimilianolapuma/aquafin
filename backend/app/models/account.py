"""Account model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.import_record import ImportRecord
    from app.models.transaction import Transaction
    from app.models.user import User


class AccountType(enum.StrEnum):
    """Supported account types."""

    bank = "bank"
    satispay = "satispay"
    paypal = "paypal"
    cash = "cash"
    investment = "investment"


class Account(Base):
    """Financial account (bank, wallet, cash, etc.)."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    type: Mapped[AccountType] = mapped_column(
        sa.Enum(AccountType, name="account_type", native_enum=False, length=20),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(sa.String(3), server_default="EUR", default="EUR")
    color: Mapped[str | None] = mapped_column(sa.String(7), nullable=True)
    icon: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.text("true"), default=True
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
    user: Mapped[User] = relationship("User", back_populates="accounts")
    transactions: Mapped[list[Transaction]] = relationship(
        "Transaction", back_populates="account", cascade="all, delete-orphan"
    )
    imports: Mapped[list[ImportRecord]] = relationship(
        "ImportRecord", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account {self.name} ({self.type.value})>"
