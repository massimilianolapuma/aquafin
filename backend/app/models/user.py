"""User model."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.categorization_rule import CategorizationRule
    from app.models.category import Category
    from app.models.import_record import ImportRecord


class User(Base):
    """Application user, linked to Clerk for authentication."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    clerk_id: Mapped[str] = mapped_column(sa.String(255), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(sa.String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    locale: Mapped[str] = mapped_column(sa.String(5), server_default="it", default="it")
    preferences: Mapped[dict[str, Any]] = mapped_column(
        sa.JSON, server_default=sa.text("'{}'::jsonb"), default=dict
    )
    is_active: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.text("true"), default=True
    )

    # Timestamps inherited from Base, redeclared for type clarity
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
    accounts: Mapped[list[Account]] = relationship(
        "Account", back_populates="user", cascade="all, delete-orphan"
    )
    categories: Mapped[list[Category]] = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    imports: Mapped[list[ImportRecord]] = relationship(
        "ImportRecord", back_populates="user", cascade="all, delete-orphan"
    )
    categorization_rules: Mapped[list[CategorizationRule]] = relationship(
        "CategorizationRule", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
