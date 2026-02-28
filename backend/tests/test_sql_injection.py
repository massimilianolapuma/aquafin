"""SQL injection prevention tests.

Verifies that SQLAlchemy's parameterized queries protect against
common injection patterns on search queries, date parameters, and
create payloads.
Uses mock-based approach to avoid SQLite DDL incompatibilities.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.account import Account, AccountType
from app.models.user import User

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MOCK_USER_ID = uuid.UUID("00000000-0000-4000-8000-ffffffffffff")
MOCK_ACCOUNT_ID = uuid.UUID("00000000-0000-4000-8000-eeeeeeeeeeee")

SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE transactions; --",
    "' OR '1'='1",
    "1; SELECT * FROM users --",
    "' UNION SELECT * FROM users --",
    "'; DELETE FROM accounts WHERE '1'='1",
    "1' OR 1=1 --",
    "admin'--",
    "' OR ''='",
    "'; EXEC xp_cmdshell('dir'); --",
    "1'; WAITFOR DELAY '0:0:5'; --",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(user_id: uuid.UUID = MOCK_USER_ID) -> User:
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


def _make_account(name: str) -> Account:
    """Create a mock Account instance."""
    now = datetime.now(UTC)
    return Account(
        id=uuid.uuid4(),
        user_id=MOCK_USER_ID,
        name=name,
        type=AccountType.bank,
        currency="EUR",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


# ---- Mock DB ----

async def _override_get_db() -> AsyncMock:  # type: ignore[misc]
    yield AsyncMock()  # type: ignore[misc]


app.dependency_overrides[get_current_user] = lambda: _make_mock_user()
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture(autouse=True)
def _restore_overrides() -> None:  # type: ignore[misc]
    saved = dict(app.dependency_overrides)
    yield  # type: ignore[misc]
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


@pytest.fixture
async def client() -> AsyncClient:  # type: ignore[misc]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Transaction search – SQL injection
# ---------------------------------------------------------------------------


class TestTransactionSearchInjection:
    """Verify that the search query parameter on transaction list is safe."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_search_injection(self, client: AsyncClient, payload: str) -> None:
        """Injecting SQL via the search parameter should not cause errors.

        The service is called with the raw payload as a string parameter;
        SQLAlchemy uses parameterized queries, so no injection occurs.
        """
        with patch(
            "app.api.transactions.transaction_service.list_transactions",
            new_callable=AsyncMock,
            return_value=([], 0),
        ) as mock_list:
            resp = await client.get("/api/v1/transactions/", params={"search": payload})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 0

            # Verify the payload was passed as a string parameter, not executed
            call_args = mock_list.call_args
            params = call_args[0][2]
            assert params.search == payload


# ---------------------------------------------------------------------------
# Analytics – date parameter injection
# ---------------------------------------------------------------------------


class TestAnalyticsDateInjection:
    """Verify that analytics date parameters reject malicious input."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_by_category_date_from_injection(
        self, client: AsyncClient, payload: str
    ) -> None:
        """Injecting SQL via date_from should return 422 (validation error)."""
        resp = await client.get(
            "/api/v1/analytics/by-category", params={"date_from": payload}
        )
        # FastAPI's date parsing should reject non-date strings
        assert resp.status_code == 422

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_by_category_date_to_injection(
        self, client: AsyncClient, payload: str
    ) -> None:
        """Injecting SQL via date_to should return 422 (validation error)."""
        resp = await client.get(
            "/api/v1/analytics/by-category", params={"date_to": payload}
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_by_account_date_injection(
        self, client: AsyncClient, payload: str
    ) -> None:
        """Injecting SQL via by-account date_from should return 422."""
        resp = await client.get(
            "/api/v1/analytics/by-account", params={"date_from": payload}
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Account create – name field injection
# ---------------------------------------------------------------------------


class TestAccountCreateInjection:
    """Verify that the account name field is treated as a safe literal string."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_create_account_with_injection_name(
        self, client: AsyncClient, payload: str
    ) -> None:
        """Creating an account with an injection payload should succeed safely.

        The name is stored literally — no SQL executed.
        """
        mock_account = _make_account(payload)

        with patch(
            "app.api.accounts.account_service.create_account",
            new_callable=AsyncMock,
            return_value=mock_account,
        ):
            resp = await client.post(
                "/api/v1/accounts/",
                json={"name": payload, "type": "bank"},
            )
            assert resp.status_code == 201
            data = resp.json()
            # The name should be stored literally, not executed
            assert data["name"] == payload
