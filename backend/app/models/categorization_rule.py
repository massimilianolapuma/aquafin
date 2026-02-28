"""Categorization rule model – user-defined rules for auto-categorization."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class MatchType(str, enum.Enum):
    """How the rule pattern is matched against transaction descriptions."""

    contains = "contains"
    exact = "exact"
    regex = "regex"
    starts_with = "starts_with"


class CategorizationRule(Base):
    """User-defined rule for automatic transaction categorization."""

    __tablename__ = "categorization_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        primary_key=True,
        server_default=sa.text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        sa.Uuid,
        sa.ForeignKey("categories.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    pattern: Mapped[str] = mapped_column(sa.String(500), nullable=False)
    match_type: Mapped[MatchType] = mapped_column(
        sa.Enum(MatchType, name="match_type", native_enum=False, length=20),
        server_default="contains",
        default=MatchType.contains,
    )
    priority: Mapped[int] = mapped_column(
        sa.Integer, server_default=sa.text("0"), default=0
    )
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
    user: Mapped[User] = relationship("User", back_populates="categorization_rules")
    category: Mapped[Category] = relationship(
        "Category", back_populates="categorization_rules"
    )

    def __repr__(self) -> str:
        return f"<CategorizationRule '{self.pattern}' ({self.match_type.value})>"
