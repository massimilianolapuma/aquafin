"""Account service – business logic for CRUD operations."""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


async def list_accounts(db: AsyncSession, user_id: UUID) -> list[Account]:
    """Return all active accounts belonging to *user_id*."""
    stmt = (
        select(Account)
        .where(Account.user_id == user_id, Account.is_active.is_(True))
        .order_by(Account.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_account(
    db: AsyncSession, user_id: UUID, data: AccountCreate
) -> Account:
    """Create a new account for *user_id*."""
    account = Account(
        user_id=user_id,
        name=data.name,
        type=data.type,
        currency=data.currency,
        color=data.color,
        icon=data.icon,
    )
    db.add(account)
    await db.flush()
    await db.refresh(account)
    return account


async def get_account(
    db: AsyncSession, user_id: UUID, account_id: UUID
) -> Account:
    """Fetch a single account ensuring it belongs to *user_id*.

    Raises 404 if the account does not exist or doesn't belong to the user.
    """
    stmt = select(Account).where(
        Account.id == account_id,
        Account.user_id == user_id,
    )
    result = await db.execute(stmt)
    account = result.scalar_one_or_none()
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return account


async def update_account(
    db: AsyncSession,
    user_id: UUID,
    account_id: UUID,
    data: AccountUpdate,
) -> Account:
    """Update mutable fields on an existing account.

    Raises 404 if the account does not exist or doesn't belong to the user.
    """
    account = await get_account(db, user_id, account_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    await db.flush()
    await db.refresh(account)
    return account


async def delete_account(
    db: AsyncSession, user_id: UUID, account_id: UUID
) -> None:
    """Soft-delete an account by setting ``is_active=False``.

    Raises 404 if the account does not exist or doesn't belong to the user.
    """
    account = await get_account(db, user_id, account_id)
    account.is_active = False
    await db.flush()
