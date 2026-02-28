"""User-related Pydantic schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserRead(BaseModel):
    """Public representation of a user."""

    id: UUID
    clerk_id: str
    email: str
    display_name: str | None = None
    locale: str
    preferences: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Fields the user may update on their own profile."""

    display_name: str | None = None
    locale: str | None = Field(default=None, min_length=2, max_length=5)
    preferences: dict[str, Any] | None = None


class ClerkWebhookPayload(BaseModel):
    """Simplified Clerk webhook event payload."""

    type: str  # "user.created", "user.updated", "user.deleted"
    data: dict[str, Any]
