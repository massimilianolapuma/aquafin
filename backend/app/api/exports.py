"""Exports API router – CSV, JSON, and GDPR data export endpoints."""

from __future__ import annotations

import io
from datetime import date, datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.export import ExportFilters, GdprExportResponse
from app.services import export_service

router = APIRouter(
    prefix="/api/v1/exports",
    tags=["exports"],
)


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


@router.get("/csv")
async def export_csv(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: UUID | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    type: str | None = Query(default=None),
) -> StreamingResponse:
    """Export user transactions as a CSV file (UTF-8 BOM for Excel)."""
    filters = ExportFilters(
        account_id=account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        type=type,
    )
    csv_content = await export_service.export_transactions_csv(
        db, current_user.id, filters
    )
    # UTF-8 BOM so Italian Excel opens the file correctly
    output = io.BytesIO(csv_content.encode("utf-8-sig"))
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"aquafin_export_{timestamp}.csv"
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------


@router.get("/json")
async def export_json(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: UUID | None = Query(default=None),
    category_id: UUID | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    type: str | None = Query(default=None),
) -> list[dict]:
    """Export user transactions as a JSON array."""
    filters = ExportFilters(
        account_id=account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        type=type,
    )
    return await export_service.export_transactions_json(
        db, current_user.id, filters
    )


# ---------------------------------------------------------------------------
# GDPR full export
# ---------------------------------------------------------------------------


@router.get("/gdpr")
async def export_gdpr(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GdprExportResponse:
    """Full GDPR data-portability export of all user data."""
    data = await export_service.export_gdpr(db, current_user.id)
    return GdprExportResponse(**data)
