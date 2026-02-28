"""Accounts API router – CRUD endpoints for financial accounts."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.account import AccountCreate, AccountList, AccountRead, AccountUpdate
from app.services import account_service

router = APIRouter(
    prefix="/api/v1/accounts",
    tags=["accounts"],
)


@router.get("/")
async def list_accounts(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountList:
    """Return all active accounts for the authenticated user."""
    accounts = await account_service.list_accounts(db, current_user.id)
    return AccountList(
        items=[AccountRead.model_validate(a) for a in accounts],
        total=len(accounts),
    )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_account(
    body: AccountCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountRead:
    """Create a new account for the authenticated user."""
    account = await account_service.create_account(db, current_user.id, body)
    return AccountRead.model_validate(account)


@router.get("/{account_id}")
async def get_account(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountRead:
    """Return a single account by ID."""
    account = await account_service.get_account(db, current_user.id, account_id)
    return AccountRead.model_validate(account)


@router.put("/{account_id}")
async def update_account(
    account_id: UUID,
    body: AccountUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountRead:
    """Update an existing account."""
    account = await account_service.update_account(
        db, current_user.id, account_id, body
    )
    return AccountRead.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Soft-delete an account (sets is_active to False)."""
    await account_service.delete_account(db, current_user.id, account_id)
