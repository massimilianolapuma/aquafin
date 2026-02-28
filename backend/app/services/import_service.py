"""Import service – upload, preview, confirm, cancel workflow."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.import_record import (
    FileType,
    ImportRecord,
    ImportStatus,
    SourceType,
)
from app.models.transaction import CategorizationMethod, Transaction, TransactionType
from app.services.categorization.engine import CategorizationEngine
from app.services.categorization.models import CategorizedTransaction
from app.services.parser.registry import ParserRegistry


def _temp_dir() -> Path:
    """Ensure the upload temp directory exists and return its path."""
    path = Path(settings.UPLOAD_TEMP_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _preview_path(import_id: UUID) -> Path:
    """Return the path for a preview JSON file."""
    return _temp_dir() / f"{import_id}.json"


def _uploaded_file_path(import_id: UUID, filename: str) -> Path:
    """Return the path to store the uploaded file."""
    return _temp_dir() / f"{import_id}_{filename}"


def _detect_file_type(filename: str) -> FileType:
    """Map file extension to FileType enum."""
    ext = Path(filename).suffix.lower()
    mapping: dict[str, FileType] = {
        ".csv": FileType.csv,
        ".pdf": FileType.pdf,
        ".xlsx": FileType.xlsx,
    }
    if ext not in mapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension: {ext}",
        )
    return mapping[ext]


def _serialize_categorized(
    transactions: list[CategorizedTransaction],
) -> list[dict[str, Any]]:
    """Serialize CategorizedTransaction list to JSON-safe dicts."""
    result: list[dict[str, Any]] = []
    for t in transactions:
        result.append(
            {
                "date": t.date.isoformat(),
                "amount": str(t.amount),
                "currency": t.currency,
                "description": t.description,
                "original_description": t.original_description,
                "type": t.type,
                "metadata": t.metadata,
                "categorization": {
                    "category_name": t.categorization.category_name,
                    "confidence": t.categorization.confidence,
                    "matched_by": t.categorization.matched_by,
                    "rule_id": t.categorization.rule_id,
                },
            }
        )
    return result


def _deserialize_categorized(
    data: list[dict[str, Any]],
) -> list[CategorizedTransaction]:
    """Deserialize dicts back into CategorizedTransaction objects."""
    from app.services.categorization.models import CategorizationResult

    result: list[CategorizedTransaction] = []
    for item in data:
        cat = item["categorization"]
        result.append(
            CategorizedTransaction(
                date=date.fromisoformat(item["date"]),
                amount=Decimal(item["amount"]),
                currency=item["currency"],
                description=item["description"],
                original_description=item["original_description"],
                type=item["type"],
                metadata=item.get("metadata", {}),
                categorization=CategorizationResult(
                    category_name=cat["category_name"],
                    confidence=cat["confidence"],
                    matched_by=cat["matched_by"],
                    rule_id=cat.get("rule_id"),
                ),
            )
        )
    return result


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------


async def upload_and_parse(
    db: AsyncSession,
    user_id: UUID,
    account_id: UUID,
    filename: str,
    content: bytes,
    source_type_hint: str | None = None,
) -> tuple[ImportRecord, list[CategorizedTransaction]]:
    """Upload a file, parse it, categorize transactions, and create a preview.

    Returns the ImportRecord and the list of categorized transactions.
    """
    file_type = _detect_file_type(filename)

    # Parse the file
    registry = ParserRegistry()
    try:
        parse_result = registry.parse(filename, content)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    # Determine source type
    try:
        source_type = SourceType(source_type_hint if source_type_hint else parse_result.source_type)
    except ValueError:
        source_type = SourceType.bank_csv

    # Categorize transactions
    engine = CategorizationEngine()
    categorized = engine.categorize_batch(parse_result.transactions)

    # Create ImportRecord
    import_record = ImportRecord(
        account_id=account_id,
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        source_type=source_type,
        status=ImportStatus.preview,
        row_count=parse_result.row_count,
        imported_count=0,
        error_log=parse_result.errors,
    )
    db.add(import_record)
    await db.flush()
    await db.refresh(import_record)

    # Save the uploaded file
    file_path = _uploaded_file_path(import_record.id, filename)
    file_path.write_bytes(content)

    # Save preview data as JSON
    preview_data = {
        "transactions": _serialize_categorized(categorized),
        "errors": parse_result.errors,
        "source_type": source_type.value,
    }
    preview_file = _preview_path(import_record.id)
    preview_file.write_text(json.dumps(preview_data, ensure_ascii=False))

    return import_record, categorized


async def get_preview(
    db: AsyncSession,
    user_id: UUID,
    import_id: UUID,
) -> tuple[ImportRecord, list[CategorizedTransaction]]:
    """Load preview data for a previously uploaded import.

    Returns the ImportRecord and the cached categorized transactions.
    """
    import_record = await _get_import_record(db, user_id, import_id)

    if import_record.status not in (ImportStatus.preview, ImportStatus.pending):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Import is in status '{import_record.status.value}', cannot preview.",
        )

    preview_file = _preview_path(import_id)
    if not preview_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview data not found – the file may have expired.",
        )

    preview_data = json.loads(preview_file.read_text())
    categorized = _deserialize_categorized(preview_data["transactions"])

    return import_record, categorized


async def confirm_import(
    db: AsyncSession,
    user_id: UUID,
    import_id: UUID,
    category_overrides: dict[int, str] | None = None,
) -> tuple[ImportRecord, int]:
    """Confirm an import – create Transaction rows and update the ImportRecord.

    *category_overrides* maps ``temp_id`` (0-based index) to a category name
    the user wants to override.
    """
    import_record = await _get_import_record(db, user_id, import_id)

    if import_record.status != ImportStatus.preview:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Import is in status '{import_record.status.value}', cannot confirm.",
        )

    preview_file = _preview_path(import_id)
    if not preview_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preview data not found – the file may have expired.",
        )

    preview_data = json.loads(preview_file.read_text())
    categorized = _deserialize_categorized(preview_data["transactions"])

    overrides = category_overrides or {}
    categorized_count = 0

    for idx, cat_tx in enumerate(categorized):
        # Apply category override if present
        matched_by = cat_tx.categorization.matched_by

        if idx in overrides:
            matched_by = "manual"

        # Determine categorization method
        method_map: dict[str, CategorizationMethod] = {
            "user_rule": CategorizationMethod.rule,
            "keyword": CategorizationMethod.keyword,
            "pattern": CategorizationMethod.pattern,
            "manual": CategorizationMethod.manual,
            "fallback": CategorizationMethod.uncategorized,
        }
        cat_method = method_map.get(matched_by, CategorizationMethod.uncategorized)

        if cat_method != CategorizationMethod.uncategorized:
            categorized_count += 1

        # Determine transaction type
        try:
            tx_type = TransactionType(cat_tx.type)
        except ValueError:
            tx_type = TransactionType.expense

        transaction = Transaction(
            account_id=import_record.account_id,
            import_id=import_record.id,
            amount=cat_tx.amount,
            currency=cat_tx.currency,
            date=cat_tx.date,
            description=cat_tx.description,
            original_description=cat_tx.original_description,
            type=tx_type,
            categorization_method=cat_method,
            metadata_extra=cat_tx.metadata,
        )
        db.add(transaction)

    # Update import record
    import_record.status = ImportStatus.confirmed
    import_record.imported_count = len(categorized)
    await db.flush()
    await db.refresh(import_record)

    # Clean up temp files
    _cleanup_temp_files(import_id, import_record.filename)

    return import_record, categorized_count


async def cancel_import(
    db: AsyncSession,
    user_id: UUID,
    import_id: UUID,
) -> None:
    """Cancel a pending/preview import and clean up temp files."""
    import_record = await _get_import_record(db, user_id, import_id)

    if import_record.status in (ImportStatus.confirmed, ImportStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Import is already '{import_record.status.value}'.",
        )

    import_record.status = ImportStatus.cancelled
    await db.flush()

    _cleanup_temp_files(import_id, import_record.filename)


async def list_imports(
    db: AsyncSession,
    user_id: UUID,
) -> list[ImportRecord]:
    """Return all imports for the given user, newest first."""
    stmt = (
        select(ImportRecord)
        .where(ImportRecord.user_id == user_id)
        .order_by(ImportRecord.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _get_import_record(
    db: AsyncSession,
    user_id: UUID,
    import_id: UUID,
) -> ImportRecord:
    """Fetch an ImportRecord ensuring it belongs to the user."""
    stmt = select(ImportRecord).where(
        ImportRecord.id == import_id,
        ImportRecord.user_id == user_id,
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import not found.",
        )
    return record


def _cleanup_temp_files(import_id: UUID, filename: str) -> None:
    """Remove preview JSON and uploaded file from temp directory."""
    preview_file = _preview_path(import_id)
    if preview_file.exists():
        preview_file.unlink()

    uploaded_file = _uploaded_file_path(import_id, filename)
    if uploaded_file.exists():
        uploaded_file.unlink()
