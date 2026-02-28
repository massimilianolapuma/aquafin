"""Tests for multi-tenant data isolation.

Verifies that one user cannot access another user's accounts,
transactions, analytics, or exports.
Uses mock-based approach to avoid SQLite DDL incompatibilities
with PostgreSQL-specific server defaults.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.account import Account, AccountType
from app.models.transaction import Transaction, TransactionType
from app.models.user import User
from app.schemas.analytics import AnalyticsSummary, AccountBreakdown, AccountBreakdownResponse
from app.schemas.export import TransactionExportRow

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_A_ID = uuid.UUID("00000000-0000-4000-8000-aaaaaaaaa001")
USER_B_ID = uuid.UUID("00000000-0000-4000-8000-bbbbbbbbb001")
ACCOUNT_A_ID = uuid.UUID("00000000-0000-4000-8000-aaaaaaaaa010")
ACCOUNT_B_ID = uuid.UUID("00000000-0000-4000-8000-bbbbbbbbb010")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(user_id: uuid.UUID) -> User:
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


def _make_account(
    account_id: uuid.UUID, user_id: uuid.UUID, name: str
) -> Account:
    """Create a mock Account instance."""
    now = datetime.now(UTC)
    return Account(
        id=account_id,
        user_id=user_id,
        name=name,
        type=AccountType.bank,
        currency="EUR",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _make_transaction(
    account_id: uuid.UUID, description: str, amount: Decimal
) -> Transaction:
    """Create a mock Transaction instance."""
    now = datetime.now(UTC)
    return Transaction(
        id=uuid.uuid4(),
        account_id=account_id,
        amount=amount,
        currency="EUR",
        date=date.today(),
        description=description,
        type=TransactionType.expense,
        is_recurring=False,
        tags=[],
        metadata_extra={},
        created_at=now,
        updated_at=now,
    )


# ---- Mock DB ----

async def _override_get_db() -> AsyncMock:  # type: ignore[misc]
    yield AsyncMock()  # type: ignore[misc]


def _set_current_user(user_id: uuid.UUID) -> None:
    """Override the authenticated user dependency."""
    app.dependency_overrides[get_current_user] = lambda: _make_mock_user(user_id)
    app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _restore_overrides() -> None:  # type: ignore[misc]
    """Save and restore app.dependency_overrides so tests don't leak state."""
    saved = dict(app.dependency_overrides)
    yield  # type: ignore[misc]
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


# ---------------------------------------------------------------------------
# Account isolation tests
# ---------------------------------------------------------------------------


class TestAccountIsolation:
    """Verify that account service is called with the correct user_id."""

    async def test_user_a_only_sees_own_accounts(self) -> None:
        """list_accounts should be called with user A's ID."""
        _set_current_user(USER_A_ID)

        accounts_a = [_make_account(ACCOUNT_A_ID, USER_A_ID, "User A Bank")]

        with patch(
            "app.api.accounts.account_service.list_accounts",
            new_callable=AsyncMock,
            return_value=accounts_a,
        ) as mock_list:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/accounts/")
                assert resp.status_code == 200
                data = resp.json()
                assert len(data["items"]) == 1
                assert data["items"][0]["name"] == "User A Bank"

            # Verify the service was called with user A's ID
            call_args = mock_list.call_args
            assert call_args[0][1] == USER_A_ID

    async def test_user_b_cannot_access_user_a_account(self) -> None:
        """get_account called as user B with user A's account_id should use user B's ID."""
        _set_current_user(USER_B_ID)

        from fastapi import HTTPException

        async def _raise_404(*args: Any, **kwargs: Any) -> None:
            raise HTTPException(status_code=404, detail="Account not found")

        with patch(
            "app.api.accounts.account_service.get_account",
            new_callable=AsyncMock,
            side_effect=_raise_404,
        ) as mock_get:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get(f"/api/v1/accounts/{ACCOUNT_A_ID}")
                assert resp.status_code == 404

            # Verify the service was called with user B's ID
            call_args = mock_get.call_args
            assert call_args[0][1] == USER_B_ID


# ---------------------------------------------------------------------------
# Transaction isolation tests
# ---------------------------------------------------------------------------


class TestTransactionIsolation:
    """Verify that transaction service is called with the correct user_id."""

    async def test_user_a_only_sees_own_transactions(self) -> None:
        """list_transactions should be called with user A's ID and return only A's data."""
        _set_current_user(USER_A_ID)

        txn_a = _make_transaction(ACCOUNT_A_ID, "User A payment", Decimal("100.00"))
        mock_result = ([txn_a], 1)

        with patch(
            "app.api.transactions.transaction_service.list_transactions",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_list:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/transactions/")
                assert resp.status_code == 200
                data = resp.json()
                assert data["total"] == 1
                assert data["items"][0]["description"] == "User A payment"

            call_args = mock_list.call_args
            assert call_args[0][1] == USER_A_ID

    async def test_user_b_only_sees_own_transactions(self) -> None:
        """list_transactions should be called with user B's ID."""
        _set_current_user(USER_B_ID)

        txn_b = _make_transaction(ACCOUNT_B_ID, "User B payment", Decimal("200.00"))
        mock_result = ([txn_b], 1)

        with patch(
            "app.api.transactions.transaction_service.list_transactions",
            new_callable=AsyncMock,
            return_value=mock_result,
        ) as mock_list:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/transactions/")
                assert resp.status_code == 200
                data = resp.json()
                assert data["total"] == 1
                assert data["items"][0]["description"] == "User B payment"

            call_args = mock_list.call_args
            assert call_args[0][1] == USER_B_ID

    async def test_cross_user_transaction_filtering(self) -> None:
        """Switching user dependency should change which user_id is passed."""
        # First as user A
        _set_current_user(USER_A_ID)
        with patch(
            "app.api.transactions.transaction_service.list_transactions",
            new_callable=AsyncMock,
            return_value=([], 0),
        ) as mock_list:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/api/v1/transactions/")
            assert mock_list.call_args[0][1] == USER_A_ID

        # Now as user B
        _set_current_user(USER_B_ID)
        with patch(
            "app.api.transactions.transaction_service.list_transactions",
            new_callable=AsyncMock,
            return_value=([], 0),
        ) as mock_list:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                await client.get("/api/v1/transactions/")
            assert mock_list.call_args[0][1] == USER_B_ID


# ---------------------------------------------------------------------------
# Analytics isolation tests
# ---------------------------------------------------------------------------


class TestAnalyticsIsolation:
    """Verify that analytics endpoints pass the authenticated user's ID."""

    async def test_summary_uses_correct_user_id(self) -> None:
        """get_summary should be called with the authenticated user's ID."""
        _set_current_user(USER_A_ID)

        mock_summary = AnalyticsSummary(
            total_income=1000.0,
            total_expenses=100.0,
            balance=900.0,
            transaction_count=2,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 2, 28),
        )

        with patch(
            "app.api.analytics.analytics_service.get_summary",
            new_callable=AsyncMock,
            return_value=mock_summary,
        ) as mock_fn:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/analytics/summary")
                assert resp.status_code == 200

            call_args = mock_fn.call_args
            assert call_args[0][1] == USER_A_ID

    async def test_by_account_uses_correct_user_id(self) -> None:
        """get_by_account should be called with the authenticated user's ID."""
        _set_current_user(USER_B_ID)

        mock_resp = AccountBreakdownResponse(items=[])

        with patch(
            "app.api.analytics.analytics_service.get_by_account",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ) as mock_fn:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/analytics/by-account")
                assert resp.status_code == 200

            call_args = mock_fn.call_args
            assert call_args[0][1] == USER_B_ID


# ---------------------------------------------------------------------------
# Export isolation tests
# ---------------------------------------------------------------------------


class TestExportIsolation:
    """Verify that export endpoints pass the authenticated user's ID."""

    async def test_csv_export_uses_correct_user_id(self) -> None:
        """export_transactions_csv should be called with user A's ID."""
        _set_current_user(USER_A_ID)

        with patch(
            "app.api.exports.export_service.export_transactions_csv",
            new_callable=AsyncMock,
            return_value="header\nrow1\n",
        ) as mock_fn:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/exports/csv")
                assert resp.status_code == 200

            call_args = mock_fn.call_args
            assert call_args[0][1] == USER_A_ID

    async def test_json_export_uses_correct_user_id(self) -> None:
        """export_transactions_json should be called with user B's ID."""
        _set_current_user(USER_B_ID)

        with patch(
            "app.api.exports.export_service.export_transactions_json",
            new_callable=AsyncMock,
            return_value=[],
        ) as mock_fn:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/exports/json")
                assert resp.status_code == 200

            call_args = mock_fn.call_args
            assert call_args[0][1] == USER_B_ID

    async def test_gdpr_export_uses_correct_user_id(self) -> None:
        """export_gdpr should be called with the authenticated user's ID."""
        _set_current_user(USER_A_ID)

        mock_gdpr = {
            "user": {},
            "accounts": [],
            "categories": [],
            "transactions": [],
            "imports": [],
            "rules": [],
            "exported_at": "2026-02-28T00:00:00+00:00",
        }

        with patch(
            "app.api.exports.export_service.export_gdpr",
            new_callable=AsyncMock,
            return_value=mock_gdpr,
        ) as mock_fn:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/exports/gdpr")
                assert resp.status_code == 200

            call_args = mock_fn.call_args
            assert call_args[0][1] == USER_A_ID
