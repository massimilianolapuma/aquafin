"""Pydantic schemas for analytics endpoints."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class AnalyticsSummary(BaseModel):
    """Overall financial summary for a given period."""

    model_config = ConfigDict(from_attributes=True)

    total_income: float = Field(description="Sum of all income transactions")
    total_expenses: float = Field(description="Sum of all expense transactions (positive value)")
    balance: float = Field(description="total_income - total_expenses")
    transaction_count: int = Field(description="Total number of transactions")
    period_start: date = Field(description="Start date of the analysis period")
    period_end: date = Field(description="End date of the analysis period")


# ---------------------------------------------------------------------------
# Category Breakdown
# ---------------------------------------------------------------------------


class CategoryBreakdown(BaseModel):
    """Expense breakdown for a single category."""

    model_config = ConfigDict(from_attributes=True)

    category_id: UUID | None = Field(description="Category UUID, None for uncategorized")
    category_name: str = Field(description="Human-readable category name")
    total: float = Field(description="Total amount spent in this category")
    count: int = Field(description="Number of transactions")
    percentage: float = Field(description="Percentage of total expenses")


class CategoryBreakdownResponse(BaseModel):
    """Response wrapper for category breakdown."""

    items: list[CategoryBreakdown]
    total_expenses: float = Field(description="Total expenses across all categories")
    period_start: date
    period_end: date


# ---------------------------------------------------------------------------
# Monthly Trend
# ---------------------------------------------------------------------------


class MonthlyTrend(BaseModel):
    """Income/expense totals for a single month."""

    model_config = ConfigDict(from_attributes=True)

    month: str = Field(description="Month in YYYY-MM format")
    income: float = Field(description="Total income for the month")
    expenses: float = Field(description="Total expenses for the month (positive value)")
    balance: float = Field(description="income - expenses")
    transaction_count: int = Field(description="Number of transactions")


class MonthlyTrendResponse(BaseModel):
    """Response wrapper for monthly trend data."""

    items: list[MonthlyTrend]


# ---------------------------------------------------------------------------
# Account Breakdown
# ---------------------------------------------------------------------------


class AccountBreakdown(BaseModel):
    """Financial breakdown for a single account."""

    model_config = ConfigDict(from_attributes=True)

    account_id: UUID = Field(description="Account UUID")
    account_name: str = Field(description="Account display name")
    total_income: float = Field(description="Total income for this account")
    total_expenses: float = Field(description="Total expenses for this account (positive)")
    balance: float = Field(description="income - expenses")
    transaction_count: int = Field(description="Number of transactions")


class AccountBreakdownResponse(BaseModel):
    """Response wrapper for account breakdown."""

    items: list[AccountBreakdown]
