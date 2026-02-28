"""Transaction service – business logic for CRUD operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.sql import func

from app.models.account import Account
from app.models.transaction import CategorizationMethod, Transaction

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.schemas.transaction import TransactionListParams, TransactionUpdate


async def list_transactions(
    db: AsyncSession,
    user_id: UUID,
    params: TransactionListParams,
) -> tuple[list[Transaction], int]:
    """Return paginated transactions belonging to *user_id* with optional filters.

    Ownership is verified by joining through the Account table.
    Returns a tuple of (items, total_count).
    """
    base = (
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(Account.user_id == user_id)
    )

    count_base = (
        select(func.count())
        .select_from(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(Account.user_id == user_id)
    )

    # Apply optional filters
    if params.account_id is not None:
        base = base.where(Transaction.account_id == params.account_id)
        count_base = count_base.where(Transaction.account_id == params.account_id)

    if params.category_id is not None:
        base = base.where(Transaction.category_id == params.category_id)
        count_base = count_base.where(Transaction.category_id == params.category_id)

    if params.date_from is not None:
        base = base.where(Transaction.date >= params.date_from)
        count_base = count_base.where(Transaction.date >= params.date_from)

    if params.date_to is not None:
        base = base.where(Transaction.date <= params.date_to)
        count_base = count_base.where(Transaction.date <= params.date_to)

    if params.type is not None:
        base = base.where(Transaction.type == params.type)
        count_base = count_base.where(Transaction.type == params.type)

    if params.search is not None:
        pattern = f"%{params.search}%"
        base = base.where(Transaction.description.ilike(pattern))
        count_base = count_base.where(Transaction.description.ilike(pattern))

    # Total count
    total_result = await db.execute(count_base)
    total = total_result.scalar_one()

    # Pagination
    offset = (params.page - 1) * params.limit
    stmt = (
        base.order_by(Transaction.date.desc(), Transaction.created_at.desc())
        .offset(offset)
        .limit(params.limit)
    )

    result = await db.execute(stmt)
    items = list(result.scalars().all())

    return items, total


async def get_transaction(
    db: AsyncSession,
    user_id: UUID,
    transaction_id: UUID,
) -> Transaction:
    """Fetch a single transaction ensuring it belongs to *user_id* via Account join.

    Raises 404 if the transaction does not exist or doesn't belong to the user.
    """
    stmt = (
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(Account.user_id == user_id, Transaction.id == transaction_id)
    )
    result = await db.execute(stmt)
    transaction = result.scalar_one_or_none()
    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


async def update_transaction(
    db: AsyncSession,
    user_id: UUID,
    transaction_id: UUID,
    data: TransactionUpdate,
) -> Transaction:
    """Update mutable fields on an existing transaction.

    Raises 404 if the transaction does not exist or doesn't belong to the user.
    """
    transaction = await get_transaction(db, user_id, transaction_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    await db.flush()
    await db.refresh(transaction)
    return transaction


async def delete_transaction(
    db: AsyncSession,
    user_id: UUID,
    transaction_id: UUID,
) -> None:
    """Hard-delete a transaction.

    Raises 404 if the transaction does not exist or doesn't belong to the user.
    """
    transaction = await get_transaction(db, user_id, transaction_id)
    await db.delete(transaction)
    await db.flush()


async def recategorize(
    db: AsyncSession,
    user_id: UUID,
    transaction_id: UUID,
    category_id: UUID,
    apply_to_similar: bool = False,
) -> Transaction:
    """Recategorize a transaction and optionally apply to similar ones.

    Similar transactions are those with the same original_description
    belonging to accounts owned by the same user.
    Sets categorization_method to 'manual'.
    """
    transaction = await get_transaction(db, user_id, transaction_id)

    transaction.category_id = category_id
    transaction.categorization_method = CategorizationMethod.manual
    await db.flush()
    await db.refresh(transaction)

    if apply_to_similar and transaction.original_description:
        # Update other transactions with the same original_description
        stmt = (
            update(Transaction)
            .where(
                Transaction.id != transaction_id,
                Transaction.original_description == transaction.original_description,
                Transaction.account_id.in_(select(Account.id).where(Account.user_id == user_id)),
            )
            .values(
                category_id=category_id,
                categorization_method=CategorizationMethod.manual,
            )
        )
        await db.execute(stmt)
        await db.flush()

    return transaction


async def bulk_categorize(
    db: AsyncSession,
    user_id: UUID,
    transaction_ids: list[UUID],
    category_id: UUID,
) -> int:
    """Bulk-update the category for a list of transactions.

    Only updates transactions that belong to accounts owned by *user_id*.
    Returns the count of updated transactions.
    """
    if not transaction_ids:
        return 0

    stmt = (
        update(Transaction)
        .where(
            Transaction.id.in_(transaction_ids),
            Transaction.account_id.in_(select(Account.id).where(Account.user_id == user_id)),
        )
        .values(
            category_id=category_id,
            categorization_method=CategorizationMethod.manual,
        )
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount  # type: ignore[no-any-return, attr-defined]
