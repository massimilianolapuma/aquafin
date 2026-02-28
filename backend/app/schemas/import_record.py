"""Pydantic schemas for file import workflow."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.import_record import FileType, ImportStatus, SourceType


# ---------------------------------------------------------------------------
# Upload response
# ---------------------------------------------------------------------------


class ImportUploadResponse(BaseModel):
    """Returned after a file has been uploaded and parsed."""

    id: UUID
    filename: str
    file_type: FileType
    source_type: SourceType
    status: ImportStatus
    row_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Preview
# ---------------------------------------------------------------------------


class TransactionPreview(BaseModel):
    """Single transaction preview row."""

    temp_id: int = Field(description="Index in the preview list (0-based)")
    date: date
    amount: float
    currency: str
    description: str
    original_description: str
    type: str
    category_name: str | None = None
    confidence: float | None = None
    matched_by: str | None = None


class ImportPreviewResponse(BaseModel):
    """Full preview of a parsed import."""

    import_id: UUID
    filename: str
    source_type: SourceType
    status: ImportStatus
    row_count: int
    transactions: list[TransactionPreview]
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------


class ImportConfirmRequest(BaseModel):
    """Body for confirming an import, with optional category overrides."""

    category_overrides: dict[int, str] = Field(
        default_factory=dict,
        description="Map temp_id → category_name to override AI suggestions",
    )


class ImportConfirmResponse(BaseModel):
    """Result after confirming an import."""

    import_id: UUID
    status: ImportStatus
    imported_count: int
    categorized_count: int


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


class ImportListItem(BaseModel):
    """Summary item for listing imports."""

    id: UUID
    filename: str
    file_type: FileType
    source_type: SourceType
    status: ImportStatus
    row_count: int
    imported_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImportListResponse(BaseModel):
    """Paginated list of imports."""

    items: list[ImportListItem]
    total: int
