"""Pydantic schemas for Account CRUD."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.account import AccountType


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class AccountCreate(BaseModel):
    """Payload for creating a new account."""

    name: str = Field(min_length=1, max_length=100)
    type: AccountType
    currency: str = Field(default="EUR", min_length=3, max_length=3)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    icon: str | None = Field(default=None, max_length=50)


class AccountUpdate(BaseModel):
    """Payload for updating an existing account (partial update)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    color: str | None = None
    icon: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AccountRead(BaseModel):
    """Single account response."""

    id: UUID
    user_id: UUID
    name: str
    type: AccountType
    currency: str
    color: str | None = None
    icon: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountList(BaseModel):
    """Paginated list of accounts."""

    items: list[AccountRead]
    total: int
