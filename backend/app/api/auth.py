"""Auth & user-profile routes."""

from __future__ import annotations

from typing import Annotated, TypeAlias

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import ClerkWebhookPayload, UserRead, UserUpdate

router = APIRouter(prefix="/api/v1", tags=["auth"])

# Annotated dependency aliases
DbSession: TypeAlias = Annotated[AsyncSession, Depends(get_db)]
CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]


# ---------------------------------------------------------------------------
# Clerk webhook – internal handlers
# ---------------------------------------------------------------------------


async def _handle_user_created(data: dict, db: AsyncSession) -> None:
    email_addresses = data.get("email_addresses", [])
    email = email_addresses[0]["email_address"] if email_addresses else ""
    user = User(
        clerk_id=data["id"],
        email=email,
        display_name=data.get("first_name") or data.get("username"),
    )
    db.add(user)
    await db.flush()


async def _handle_user_updated(data: dict, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.clerk_id == data["id"]))
    user = result.scalar_one_or_none()
    if user is None:
        return
    email_addresses = data.get("email_addresses", [])
    if email_addresses:
        user.email = email_addresses[0]["email_address"]
    if "first_name" in data:
        user.display_name = data.get("first_name") or data.get("username")


async def _handle_user_deleted(data: dict, db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.clerk_id == data["id"]))
    user = result.scalar_one_or_none()
    if user is not None:
        await db.delete(user)
        await db.flush()


_WEBHOOK_HANDLERS = {
    "user.created": _handle_user_created,
    "user.updated": _handle_user_updated,
    "user.deleted": _handle_user_deleted,
}


# ---------------------------------------------------------------------------
# Clerk webhook
# ---------------------------------------------------------------------------


@router.post("/auth/webhook", status_code=status.HTTP_200_OK)
async def clerk_webhook(
    payload: ClerkWebhookPayload,
    db: DbSession,
) -> dict[str, str]:
    """Handle Clerk webhook events for user synchronisation.

    .. todo:: Add Svix webhook signature verification for production.
    """
    handler = _WEBHOOK_HANDLERS.get(payload.type)
    if handler is not None:
        await handler(payload.data, db)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------


@router.get("/users/me", response_model=UserRead)
async def get_me(user: CurrentUser) -> User:
    """Return the authenticated user's profile."""
    return user


@router.put("/users/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    user: CurrentUser,
    db: DbSession,
) -> User:
    """Update the authenticated user's profile (partial update)."""
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/users/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    user: CurrentUser,
    db: DbSession,
) -> Response:
    """Delete the authenticated user and all related data (GDPR)."""
    await db.delete(user)
    await db.flush()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
