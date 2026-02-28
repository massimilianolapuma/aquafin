"""Pydantic schemas for data export endpoints."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Filter schema
# ---------------------------------------------------------------------------


class ExportFilters(BaseModel):
    """Query-string filters for transaction exports."""

    account_id: UUID | None = None
    category_id: UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    type: str | None = None


# ---------------------------------------------------------------------------
# Row / item schemas
# ---------------------------------------------------------------------------


class TransactionExportRow(BaseModel):
    """Single transaction row in an export payload."""

    date: date
    description: str | None = None
    amount: Decimal
    currency: str
    type: str
    category_name: str | None = None
    account_name: str
    categorization_method: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# GDPR full-export schema
# ---------------------------------------------------------------------------


class GdprExportResponse(BaseModel):
    """Complete GDPR data-portability export for a single user."""

    user: dict[str, Any]
    accounts: list[dict[str, Any]]
    categories: list[dict[str, Any]]
    transactions: list[dict[str, Any]]
    imports: list[dict[str, Any]]
    rules: list[dict[str, Any]]
    exported_at: datetime
