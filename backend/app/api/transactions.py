"""Transactions API router – CRUD, filters, bulk categorization."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.auth import get_current_user
from app.core.database import get_db
from app.schemas.transaction import (
    BulkCategorizeRequest,
    BulkCategorizeResponse,
    RecategorizeRequest,
    TransactionListParams,
    TransactionListResponse,
    TransactionRead,
    TransactionUpdate,
)
from app.services import transaction_service

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.models.user import User

router = APIRouter(
    prefix="/api/v1/transactions",
    tags=["transactions"],
)


@router.get("/")
async def list_transactions(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: Annotated[UUID | None, Query()] = None,
    category_id: Annotated[UUID | None, Query()] = None,
    date_from: Annotated[str | None, Query(alias="date_from")] = None,
    date_to: Annotated[str | None, Query(alias="date_to")] = None,
    type: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> TransactionListResponse:
    """Return paginated transactions for the authenticated user with optional filters."""
    from datetime import date as date_type

    params = TransactionListParams(
        account_id=account_id,
        category_id=category_id,
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        type=type,
        search=search,
        page=page,
        limit=limit,
    )
    items, total = await transaction_service.list_transactions(
        db, current_user.id, params
    )
    return TransactionListResponse(
        items=[TransactionRead.model_validate(t) for t in items],
        total=total,
        page=params.page,
        limit=params.limit,
    )


@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionRead:
    """Return a single transaction by ID."""
    transaction = await transaction_service.get_transaction(
        db, current_user.id, transaction_id
    )
    return TransactionRead.model_validate(transaction)


@router.put("/{transaction_id}")
async def update_transaction(
    transaction_id: UUID,
    body: TransactionUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionRead:
    """Update an existing transaction."""
    transaction = await transaction_service.update_transaction(
        db, current_user.id, transaction_id, body
    )
    return TransactionRead.model_validate(transaction)


@router.post("/{transaction_id}/recategorize")
async def recategorize_transaction(
    transaction_id: UUID,
    body: RecategorizeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionRead:
    """Recategorize a transaction, optionally applying to similar ones."""
    transaction = await transaction_service.recategorize(
        db, current_user.id, transaction_id, body.category_id, body.apply_to_similar
    )
    return TransactionRead.model_validate(transaction)


@router.post("/bulk-categorize")
async def bulk_categorize(
    body: BulkCategorizeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BulkCategorizeResponse:
    """Bulk-categorize multiple transactions at once."""
    count = await transaction_service.bulk_categorize(
        db, current_user.id, body.transaction_ids, body.category_id
    )
    return BulkCategorizeResponse(updated_count=count)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a transaction (hard delete)."""
    await transaction_service.delete_transaction(
        db, current_user.id, transaction_id
    )
