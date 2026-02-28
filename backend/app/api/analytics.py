"""Analytics API router – financial statistics and aggregations."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.analytics import (
    AccountBreakdownResponse,
    AnalyticsSummary,
    CategoryBreakdownResponse,
    MonthlyTrendResponse,
)
from app.services import analytics_service

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
)


@router.get("/summary")
async def get_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    period: Annotated[str, Query(description="month | quarter | year")] = "month",
) -> AnalyticsSummary:
    """Return income/expense summary for the requested period."""
    return await analytics_service.get_summary(db, current_user.id, period)


@router.get("/by-category")
async def get_by_category(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: Annotated[date | None, Query(description="Start date (YYYY-MM-DD)")] = None,
    date_to: Annotated[date | None, Query(description="End date (YYYY-MM-DD)")] = None,
) -> CategoryBreakdownResponse:
    """Return expense breakdown grouped by category."""
    return await analytics_service.get_by_category(db, current_user.id, date_from, date_to)


@router.get("/by-month")
async def get_by_month(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    months: Annotated[int, Query(ge=1, le=36, description="Number of months")] = 12,
) -> MonthlyTrendResponse:
    """Return monthly income/expense trend."""
    return await analytics_service.get_by_month(db, current_user.id, months)


@router.get("/by-account")
async def get_by_account(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    date_from: Annotated[date | None, Query(description="Start date (YYYY-MM-DD)")] = None,
    date_to: Annotated[date | None, Query(description="End date (YYYY-MM-DD)")] = None,
) -> AccountBreakdownResponse:
    """Return financial breakdown grouped by account."""
    return await analytics_service.get_by_account(db, current_user.id, date_from, date_to)
