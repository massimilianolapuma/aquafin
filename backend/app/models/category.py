"""Category model (hierarchical, supports system + user-defined)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.categorization_rule import CategorizationRule
    from app.models.transaction import Transaction
    from app.models.user import User


class Category(Base):
    """Transaction category with hierarchy support."""

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name_key: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    name_custom: Mapped[str | None] = mapped_column(sa.String(100), nullable=True)
    icon: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(sa.String(7), nullable=True)
    is_system: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.text("false"), default=False
    )
    is_income: Mapped[bool] = mapped_column(
        sa.Boolean, server_default=sa.text("false"), default=False
    )
    sort_order: Mapped[int] = mapped_column(sa.Integer, server_default=sa.text("0"), default=0)

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
    user: Mapped[User | None] = relationship("User", back_populates="categories")
    parent: Mapped[Category | None] = relationship(
        "Category",
        back_populates="children",
        remote_side="Category.id",
    )
    children: Mapped[list[Category]] = relationship(
        "Category", back_populates="parent", cascade="all, delete-orphan"
    )
    transactions: Mapped[list[Transaction]] = relationship("Transaction", back_populates="category")
    categorization_rules: Mapped[list[CategorizationRule]] = relationship(
        "CategorizationRule", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category {self.name_key}>"
