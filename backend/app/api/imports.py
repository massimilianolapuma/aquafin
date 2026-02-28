"""Imports API router – upload, preview, confirm, cancel workflow."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.params import Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.import_record import (
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportListItem,
    ImportListResponse,
    ImportPreviewResponse,
    ImportUploadResponse,
    TransactionPreview,
)
from app.services import import_service

router = APIRouter(
    prefix="/api/v1/imports",
    tags=["imports"],
)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    account_id: Annotated[UUID, Form()],
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    source_type: Annotated[str | None, Form()] = None,
) -> ImportUploadResponse:
    """Upload a file for parsing and preview.

    Accepts CSV, PDF, or XLSX files up to the configured max size.
    Returns the import record with preview status.
    """
    # Validate file size
    content = await file.read()
    max_bytes = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum size of {settings.UPLOAD_MAX_SIZE_MB}MB.",
        )

    filename = file.filename or "unknown"
    import_record, _ = await import_service.upload_and_parse(
        db=db,
        user_id=current_user.id,
        account_id=account_id,
        filename=filename,
        content=content,
        source_type_hint=source_type,
    )

    return ImportUploadResponse.model_validate(import_record)


@router.get("/{import_id}/preview")
async def get_preview(
    import_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportPreviewResponse:
    """Return the parsed and categorized preview for an import."""
    import_record, categorized = await import_service.get_preview(
        db=db,
        user_id=current_user.id,
        import_id=import_id,
    )

    transactions = [
        TransactionPreview(
            temp_id=idx,
            date=ct.date,
            amount=float(ct.amount),
            currency=ct.currency,
            description=ct.description,
            original_description=ct.original_description,
            type=ct.type,
            category_name=ct.categorization.category_name,
            confidence=ct.categorization.confidence,
            matched_by=ct.categorization.matched_by,
        )
        for idx, ct in enumerate(categorized)
    ]

    return ImportPreviewResponse(
        import_id=import_record.id,
        filename=import_record.filename,
        source_type=import_record.source_type,
        status=import_record.status,
        row_count=import_record.row_count,
        transactions=transactions,
        errors=import_record.error_log or [],
    )


@router.post("/{import_id}/confirm")
async def confirm_import(
    import_id: UUID,
    body: ImportConfirmRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportConfirmResponse:
    """Confirm an import – persist all transactions to the database."""
    import_record, categorized_count = await import_service.confirm_import(
        db=db,
        user_id=current_user.id,
        import_id=import_id,
        category_overrides=body.category_overrides,
    )

    return ImportConfirmResponse(
        import_id=import_record.id,
        status=import_record.status,
        imported_count=import_record.imported_count,
        categorized_count=categorized_count,
    )


@router.delete("/{import_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_import(
    import_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel a pending/preview import and clean up temp files."""
    await import_service.cancel_import(
        db=db,
        user_id=current_user.id,
        import_id=import_id,
    )


@router.get("/")
async def list_imports(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ImportListResponse:
    """List all imports for the authenticated user."""
    records = await import_service.list_imports(
        db=db,
        user_id=current_user.id,
    )
    return ImportListResponse(
        items=[ImportListItem.model_validate(r) for r in records],
        total=len(records),
    )
