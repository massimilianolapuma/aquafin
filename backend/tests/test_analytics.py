"""Tests for the Analytics API."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.user import User
from app.schemas.analytics import (
    AccountBreakdown,
    AccountBreakdownResponse,
    AnalyticsSummary,
    CategoryBreakdown,
    CategoryBreakdownResponse,
    MonthlyTrend,
    MonthlyTrendResponse,
)
from app.services import analytics_service

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

MOCK_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
MOCK_ACCOUNT_ID = uuid.UUID("00000000-0000-4000-8000-000000000010")
MOCK_ACCOUNT_ID_2 = uuid.UUID("00000000-0000-4000-8000-000000000011")
MOCK_CATEGORY_ID = uuid.UUID("00000000-0000-4000-8000-000000000020")
MOCK_CATEGORY_ID_2 = uuid.UUID("00000000-0000-4000-8000-000000000021")


def _make_mock_user(user_id: uuid.UUID = MOCK_USER_ID) -> User:
    """Create a lightweight User instance for dependency overrides."""
    now = datetime.now(UTC)
    return User(
        id=user_id,
        clerk_id=f"clerk_{user_id.hex[:8]}",
        email=f"{user_id.hex[:8]}@test.com",
        display_name="Test User",
        locale="en",
        preferences={},
        is_active=True,
        created_at=now,
        updated_at=now,
    )


# ---- Dependency overrides ----


async def _override_get_db() -> AsyncMock:  # type: ignore[misc]
    yield AsyncMock()  # type: ignore[misc]


app.dependency_overrides[get_current_user] = lambda: _make_mock_user()
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
async def client() -> AsyncClient:  # type: ignore[misc]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Mock return values
# ---------------------------------------------------------------------------

_MOCK_SUMMARY = AnalyticsSummary(
    total_income=3000.0,
    total_expenses=225.0,
    balance=2775.0,
    transaction_count=4,
    period_start=date(2026, 2, 1),
    period_end=date(2026, 2, 28),
)

_MOCK_SUMMARY_EMPTY = AnalyticsSummary(
    total_income=0,
    total_expenses=0,
    balance=0,
    transaction_count=0,
    period_start=date(2026, 2, 1),
    period_end=date(2026, 2, 28),
)

_MOCK_SUMMARY_QUARTER = AnalyticsSummary(
    total_income=6000.0,
    total_expenses=425.0,
    balance=5575.0,
    transaction_count=6,
    period_start=date(2025, 12, 1),
    period_end=date(2026, 2, 28),
)

_MOCK_SUMMARY_YEAR = AnalyticsSummary(
    total_income=6000.0,
    total_expenses=425.0,
    balance=5575.0,
    transaction_count=6,
    period_start=date(2025, 3, 1),
    period_end=date(2026, 2, 28),
)

_MOCK_CATEGORY_RESP = CategoryBreakdownResponse(
    items=[
        CategoryBreakdown(
            category_id=MOCK_CATEGORY_ID,
            category_name="groceries",
            total=200.0,
            count=2,
            percentage=88.89,
        ),
        CategoryBreakdown(
            category_id=None,
            category_name="Uncategorized",
            total=25.0,
            count=1,
            percentage=11.11,
        ),
    ],
    total_expenses=225.0,
    period_start=date(2026, 2, 1),
    period_end=date(2026, 2, 28),
)

_MOCK_MONTHLY_RESP = MonthlyTrendResponse(
    items=[
        MonthlyTrend(
            month="2026-01",
            income=3000.0,
            expenses=200.0,
            balance=2800.0,
            transaction_count=2,
        ),
        MonthlyTrend(
            month="2026-02",
            income=3000.0,
            expenses=225.0,
            balance=2775.0,
            transaction_count=4,
        ),
    ]
)

_MOCK_ACCOUNT_RESP = AccountBreakdownResponse(
    items=[
        AccountBreakdown(
            account_id=MOCK_ACCOUNT_ID,
            account_name="Main Bank",
            total_income=3000.0,
            total_expenses=175.0,
            balance=2825.0,
            transaction_count=3,
        ),
        AccountBreakdown(
            account_id=MOCK_ACCOUNT_ID_2,
            account_name="PayPal",
            total_income=0.0,
            total_expenses=50.0,
            balance=-50.0,
            transaction_count=1,
        ),
    ]
)


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestAnalyticsSchemas:
    """Pydantic schema validation."""

    def test_summary_valid(self) -> None:
        """AnalyticsSummary accepts correct data."""
        s = AnalyticsSummary(
            total_income=5000.0,
            total_expenses=2000.0,
            balance=3000.0,
            transaction_count=10,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )
        assert s.balance == 3000.0

    def test_summary_zero(self) -> None:
        """AnalyticsSummary works with zeros."""
        s = AnalyticsSummary(
            total_income=0,
            total_expenses=0,
            balance=0,
            transaction_count=0,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )
        assert s.transaction_count == 0

    def test_category_breakdown_valid(self) -> None:
        """CategoryBreakdown with null category_id."""
        cb = CategoryBreakdown(
            category_id=None,
            category_name="Uncategorized",
            total=100.0,
            count=5,
            percentage=33.33,
        )
        assert cb.category_id is None

    def test_category_breakdown_with_id(self) -> None:
        """CategoryBreakdown with a valid category_id."""
        cb = CategoryBreakdown(
            category_id=MOCK_CATEGORY_ID,
            category_name="Groceries",
            total=250.0,
            count=3,
            percentage=66.67,
        )
        assert cb.category_id == MOCK_CATEGORY_ID

    def test_monthly_trend_valid(self) -> None:
        """MonthlyTrend accepts YYYY-MM format."""
        mt = MonthlyTrend(
            month="2025-06",
            income=3000,
            expenses=1500,
            balance=1500,
            transaction_count=20,
        )
        assert mt.month == "2025-06"

    def test_account_breakdown_valid(self) -> None:
        """AccountBreakdown validates correctly."""
        ab = AccountBreakdown(
            account_id=MOCK_ACCOUNT_ID,
            account_name="Main Bank",
            total_income=5000,
            total_expenses=2000,
            balance=3000,
            transaction_count=15,
        )
        assert ab.balance == 3000

    def test_category_breakdown_response_valid(self) -> None:
        """CategoryBreakdownResponse wraps items correctly."""
        resp = CategoryBreakdownResponse(
            items=[],
            total_expenses=0,
            period_start=date(2025, 1, 1),
            period_end=date(2025, 1, 31),
        )
        assert resp.items == []

    def test_monthly_trend_response_valid(self) -> None:
        """MonthlyTrendResponse wraps items correctly."""
        resp = MonthlyTrendResponse(items=[])
        assert resp.items == []

    def test_account_breakdown_response_valid(self) -> None:
        """AccountBreakdownResponse wraps items correctly."""
        resp = AccountBreakdownResponse(items=[])
        assert resp.items == []


# ---------------------------------------------------------------------------
# Service unit tests (_period_range helper)
# ---------------------------------------------------------------------------


class TestPeriodRange:
    """Test the _period_range helper function."""

    def test_month_period(self) -> None:
        """Month period starts on day 1 of current month."""
        start, end = analytics_service._period_range("month")
        assert start.day == 1
        assert end == date.today()

    def test_quarter_period(self) -> None:
        """Quarter period spans roughly 3 months."""
        start, end = analytics_service._period_range("quarter")
        assert start.day == 1
        assert (end - start).days >= 60

    def test_year_period(self) -> None:
        """Year period spans roughly 12 months."""
        start, end = analytics_service._period_range("year")
        assert start.day == 1
        assert (end - start).days >= 300

    def test_unknown_period_defaults_to_month(self) -> None:
        """Unknown period falls back to month."""
        start, end = analytics_service._period_range("unknown")
        start_m, end_m = analytics_service._period_range("month")
        assert start == start_m
        assert end == end_m


# ---------------------------------------------------------------------------
# API endpoint tests (service layer mocked)
# ---------------------------------------------------------------------------


class TestAnalyticsEndpoints:
    """HTTP-level tests for analytics router."""

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_summary", new_callable=AsyncMock)
    async def test_summary_default(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /summary returns 200 with default period."""
        mock_svc.return_value = _MOCK_SUMMARY
        resp = await client.get("/api/v1/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_income"] == 3000.0
        assert data["total_expenses"] == 225.0
        assert data["balance"] == 2775.0
        assert data["transaction_count"] == 4
        mock_svc.assert_awaited_once()

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_summary", new_callable=AsyncMock)
    async def test_summary_quarter_param(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /summary?period=quarter returns 200."""
        mock_svc.return_value = _MOCK_SUMMARY_QUARTER
        resp = await client.get("/api/v1/analytics/summary", params={"period": "quarter"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_income"] == 6000.0
        assert data["transaction_count"] == 6

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_summary", new_callable=AsyncMock)
    async def test_summary_year_param(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /summary?period=year returns 200."""
        mock_svc.return_value = _MOCK_SUMMARY_YEAR
        resp = await client.get("/api/v1/analytics/summary", params={"period": "year"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_income"] == 6000.0

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_summary", new_callable=AsyncMock)
    async def test_summary_empty(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /summary with no data returns zeros."""
        mock_svc.return_value = _MOCK_SUMMARY_EMPTY
        resp = await client.get("/api/v1/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_income"] == 0
        assert data["transaction_count"] == 0

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_by_category", new_callable=AsyncMock)
    async def test_by_category_endpoint(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /by-category returns 200 with correct structure."""
        mock_svc.return_value = _MOCK_CATEGORY_RESP
        resp = await client.get("/api/v1/analytics/by-category")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total_expenses" in data
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_by_category", new_callable=AsyncMock)
    async def test_by_category_with_dates(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /by-category passes date filters."""
        mock_svc.return_value = _MOCK_CATEGORY_RESP
        resp = await client.get(
            "/api/v1/analytics/by-category",
            params={"date_from": "2026-01-01", "date_to": "2026-02-28"},
        )
        assert resp.status_code == 200
        mock_svc.assert_awaited_once()

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_by_category", new_callable=AsyncMock)
    async def test_by_category_uncategorized(
        self, mock_svc: AsyncMock, client: AsyncClient
    ) -> None:
        """Uncategorized items appear with null category_id."""
        mock_svc.return_value = _MOCK_CATEGORY_RESP
        resp = await client.get("/api/v1/analytics/by-category")
        data = resp.json()
        uncategorized = [i for i in data["items"] if i["category_id"] is None]
        assert len(uncategorized) == 1
        assert uncategorized[0]["total"] == 25.0

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_by_month", new_callable=AsyncMock)
    async def test_by_month_endpoint(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /by-month returns 200."""
        mock_svc.return_value = _MOCK_MONTHLY_RESP
        resp = await client.get("/api/v1/analytics/by-month")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_by_month", new_callable=AsyncMock)
    async def test_by_month_custom_months(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /by-month?months=3 returns 200."""
        mock_svc.return_value = _MOCK_MONTHLY_RESP
        resp = await client.get("/api/v1/analytics/by-month", params={"months": 3})
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_by_month_invalid_months_zero(self, client: AsyncClient) -> None:
        """GET /by-month?months=0 returns 422 (validation error)."""
        resp = await client.get("/api/v1/analytics/by-month", params={"months": 0})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_by_month_invalid_months_too_high(self, client: AsyncClient) -> None:
        """GET /by-month?months=100 returns 422 (validation error)."""
        resp = await client.get("/api/v1/analytics/by-month", params={"months": 100})
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_by_account", new_callable=AsyncMock)
    async def test_by_account_endpoint(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /by-account returns 200."""
        mock_svc.return_value = _MOCK_ACCOUNT_RESP
        resp = await client.get("/api/v1/analytics/by-account")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    @patch.object(analytics_service, "get_by_account", new_callable=AsyncMock)
    async def test_by_account_names(self, mock_svc: AsyncMock, client: AsyncClient) -> None:
        """GET /by-account returns correct account names."""
        mock_svc.return_value = _MOCK_ACCOUNT_RESP
        resp = await client.get("/api/v1/analytics/by-account")
        data = resp.json()
        names = {i["account_name"] for i in data["items"]}
        assert "Main Bank" in names
        assert "PayPal" in names

    @pytest.mark.asyncio
    async def test_unauthorized_summary(self) -> None:
        """GET /summary without auth returns 401/403/422."""
        original = app.dependency_overrides.copy()
        app.dependency_overrides.pop(get_current_user, None)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/analytics/summary")
            assert resp.status_code in (401, 403, 422)
        finally:
            app.dependency_overrides.update(original)

    @pytest.mark.asyncio
    async def test_unauthorized_by_category(self) -> None:
        """GET /by-category without auth returns 401/403/422."""
        original = app.dependency_overrides.copy()
        app.dependency_overrides.pop(get_current_user, None)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/analytics/by-category")
            assert resp.status_code in (401, 403, 422)
        finally:
            app.dependency_overrides.update(original)

    @pytest.mark.asyncio
    async def test_unauthorized_by_month(self) -> None:
        """GET /by-month without auth returns 401/403/422."""
        original = app.dependency_overrides.copy()
        app.dependency_overrides.pop(get_current_user, None)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/analytics/by-month")
            assert resp.status_code in (401, 403, 422)
        finally:
            app.dependency_overrides.update(original)

    @pytest.mark.asyncio
    async def test_unauthorized_by_account(self) -> None:
        """GET /by-account without auth returns 401/403/422."""
        original = app.dependency_overrides.copy()
        app.dependency_overrides.pop(get_current_user, None)
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/analytics/by-account")
            assert resp.status_code in (401, 403, 422)
        finally:
            app.dependency_overrides.update(original)
