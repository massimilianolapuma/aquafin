"""Analytics service – financial statistics and aggregations."""

from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction, TransactionType
from app.schemas.analytics import (
    AccountBreakdown,
    AccountBreakdownResponse,
    AnalyticsSummary,
    CategoryBreakdown,
    CategoryBreakdownResponse,
    MonthlyTrend,
    MonthlyTrendResponse,
)


def _period_range(period: str) -> tuple[date, date]:
    """Return (start, end) date range for a named period.

    Supported values: ``month``, ``quarter``, ``year``.
    """
    today = date.today()
    if period == "month":
        start = today.replace(day=1)
    elif period == "quarter":
        start = (today.replace(day=1) - timedelta(days=60)).replace(day=1)
    elif period == "year":
        start = (today.replace(day=1) - timedelta(days=335)).replace(day=1)
    else:
        start = today.replace(day=1)
    return start, today


async def get_summary(
    db: AsyncSession,
    user_id: UUID,
    period: str = "month",
) -> AnalyticsSummary:
    """Return aggregated income, expenses, and balance for *period*.

    :param db: Async database session.
    :param user_id: Authenticated user ID.
    :param period: One of ``month``, ``quarter``, ``year``.
    """
    period_start, period_end = _period_range(period)

    stmt = (
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.income, Transaction.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.expense, func.abs(Transaction.amount)),
                        else_=0,
                    )
                ),
                0,
            ).label("total_expenses"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Account.user_id == user_id,
            Transaction.date >= period_start,
            Transaction.date <= period_end,
        )
    )

    result = await db.execute(stmt)
    row = result.one()

    total_income = float(row.total_income)
    total_expenses = float(row.total_expenses)

    return AnalyticsSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        balance=total_income - total_expenses,
        transaction_count=row.transaction_count,
        period_start=period_start,
        period_end=period_end,
    )


async def get_by_category(
    db: AsyncSession,
    user_id: UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> CategoryBreakdownResponse:
    """Return expense breakdown grouped by category.

    :param db: Async database session.
    :param user_id: Authenticated user ID.
    :param date_from: Optional start date filter.
    :param date_to: Optional end date filter.
    """
    today = date.today()
    if date_from is None:
        date_from = today.replace(day=1)
    if date_to is None:
        date_to = today

    stmt = (
        select(
            Transaction.category_id,
            func.coalesce(Category.name_custom, Category.name_key, "Uncategorized").label(
                "category_name"
            ),
            func.sum(func.abs(Transaction.amount)).label("total"),
            func.count(Transaction.id).label("count"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(
            Account.user_id == user_id,
            Transaction.type == TransactionType.expense,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by(Transaction.category_id, "category_name")
    )

    result = await db.execute(stmt)
    rows = result.all()

    total_expenses = sum(float(r.total) for r in rows) if rows else 0.0

    items = [
        CategoryBreakdown(
            category_id=r.category_id,
            category_name=r.category_name,
            total=float(r.total),
            count=r.count,
            percentage=round(float(r.total) / total_expenses * 100, 2) if total_expenses else 0.0,
        )
        for r in rows
    ]

    return CategoryBreakdownResponse(
        items=items,
        total_expenses=total_expenses,
        period_start=date_from,
        period_end=date_to,
    )


async def get_by_month(
    db: AsyncSession,
    user_id: UUID,
    months: int = 12,
) -> MonthlyTrendResponse:
    """Return monthly income/expense trend for the last *months* months.

    :param db: Async database session.
    :param user_id: Authenticated user ID.
    :param months: Number of months to include (1–36).
    """
    today = date.today()
    start = (today.replace(day=1) - timedelta(days=30 * (months - 1))).replace(day=1)

    year_col = func.extract("year", Transaction.date).label("yr")
    month_col = func.extract("month", Transaction.date).label("mo")

    stmt = (
        select(
            year_col,
            month_col,
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.income, Transaction.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("income"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.expense, func.abs(Transaction.amount)),
                        else_=0,
                    )
                ),
                0,
            ).label("expenses"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Account.user_id == user_id,
            Transaction.date >= start,
            Transaction.date <= today,
        )
        .group_by(year_col, month_col)
        .order_by(year_col, month_col)
    )

    result = await db.execute(stmt)
    rows = result.all()

    items = [
        MonthlyTrend(
            month=f"{int(r.yr):04d}-{int(r.mo):02d}",
            income=float(r.income),
            expenses=float(r.expenses),
            balance=float(r.income) - float(r.expenses),
            transaction_count=r.transaction_count,
        )
        for r in rows
    ]

    return MonthlyTrendResponse(items=items)


async def get_by_account(
    db: AsyncSession,
    user_id: UUID,
    date_from: date | None = None,
    date_to: date | None = None,
) -> AccountBreakdownResponse:
    """Return financial breakdown grouped by account.

    :param db: Async database session.
    :param user_id: Authenticated user ID.
    :param date_from: Optional start date filter.
    :param date_to: Optional end date filter.
    """
    today = date.today()
    if date_from is None:
        date_from = today.replace(day=1)
    if date_to is None:
        date_to = today

    stmt = (
        select(
            Account.id.label("account_id"),
            Account.name.label("account_name"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.income, Transaction.amount),
                        else_=0,
                    )
                ),
                0,
            ).label("total_income"),
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.type == TransactionType.expense, func.abs(Transaction.amount)),
                        else_=0,
                    )
                ),
                0,
            ).label("total_expenses"),
            func.count(Transaction.id).label("transaction_count"),
        )
        .join(Account, Transaction.account_id == Account.id)
        .where(
            Account.user_id == user_id,
            Transaction.date >= date_from,
            Transaction.date <= date_to,
        )
        .group_by(Account.id, Account.name)
    )

    result = await db.execute(stmt)
    rows = result.all()

    items = [
        AccountBreakdown(
            account_id=r.account_id,
            account_name=r.account_name,
            total_income=float(r.total_income),
            total_expenses=float(r.total_expenses),
            balance=float(r.total_income) - float(r.total_expenses),
            transaction_count=r.transaction_count,
        )
        for r in rows
    ]

    return AccountBreakdownResponse(items=items)
