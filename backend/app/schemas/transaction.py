"""Pydantic schemas for Transaction CRUD."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class TransactionRead(BaseModel):
    """Single transaction response."""

    id: UUID
    account_id: UUID
    category_id: UUID | None = None
    import_id: UUID | None = None
    amount: float
    currency: str
    date: date
    description: str | None = None
    original_description: str | None = None
    type: str
    categorization_method: str | None = None
    is_recurring: bool
    tags: list[str]
    metadata_extra: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""

    items: list[TransactionRead]
    total: int
    page: int
    limit: int


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TransactionUpdate(BaseModel):
    """Payload for updating an existing transaction (partial update)."""

    category_id: UUID | None = None
    description: str | None = None
    tags: list[str] | None = None
    is_recurring: bool | None = None


class TransactionListParams(BaseModel):
    """Query parameters for listing transactions."""

    account_id: UUID | None = None
    category_id: UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    type: str | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class RecategorizeRequest(BaseModel):
    """Payload for recategorizing a transaction."""

    category_id: UUID
    apply_to_similar: bool = False


class BulkCategorizeRequest(BaseModel):
    """Payload for bulk-categorizing multiple transactions."""

    transaction_ids: list[UUID]
    category_id: UUID


class BulkCategorizeResponse(BaseModel):
    """Response for bulk categorization."""

    updated_count: int
