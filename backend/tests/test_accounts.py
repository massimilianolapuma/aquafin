"""Tests for the Accounts CRUD API."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.account import AccountType
from app.models.user import User
from app.schemas.account import AccountCreate, AccountUpdate

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

MOCK_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
OTHER_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")


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


# ---- In-memory SQLite async session ----

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models.base import Base

_engine = create_async_engine("sqlite+aiosqlite://", echo=False)
_TestSession = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _setup_db() -> None:  # type: ignore[misc]
    """Create all tables before each test, drop after."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield  # type: ignore[misc]
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db() -> AsyncSession:  # type: ignore[misc]
    async with _TestSession() as session:
        try:
            yield session  # type: ignore[misc]
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Apply dependency overrides
app.dependency_overrides[get_current_user] = lambda: _make_mock_user()
app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
async def client() -> AsyncClient:  # type: ignore[misc]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestAccountSchemas:
    """Pydantic schema edge-case validation."""

    def test_create_valid(self) -> None:
        data = AccountCreate(name="Bank", type=AccountType.bank)
        assert data.currency == "EUR"

    def test_create_name_too_long(self) -> None:
        with pytest.raises(ValidationError):
            AccountCreate(name="x" * 101, type=AccountType.bank)

    def test_create_name_empty(self) -> None:
        with pytest.raises(ValidationError):
            AccountCreate(name="", type=AccountType.bank)

    def test_create_bad_color(self) -> None:
        with pytest.raises(ValidationError):
            AccountCreate(name="X", type=AccountType.bank, color="red")

    def test_create_valid_color(self) -> None:
        data = AccountCreate(name="X", type=AccountType.bank, color="#aaBB00")
        assert data.color == "#aaBB00"

    def test_create_bad_currency(self) -> None:
        with pytest.raises(ValidationError):
            AccountCreate(name="X", type=AccountType.bank, currency="EURO")

    def test_update_partial(self) -> None:
        data = AccountUpdate(name="New")
        assert data.currency is None
        assert data.is_active is None


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------


class TestAccountsAPI:
    """End-to-end tests via the HTTP API."""

    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/accounts/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0

    @pytest.mark.asyncio
    async def test_create_and_get(self, client: AsyncClient) -> None:
        # Create
        payload = {"name": "Main Bank", "type": "bank", "currency": "EUR"}
        resp = await client.post("/api/v1/accounts/", json=payload)
        assert resp.status_code == 201
        created = resp.json()
        assert created["name"] == "Main Bank"
        assert created["type"] == "bank"
        assert created["is_active"] is True
        account_id = created["id"]

        # Get
        resp = await client.get(f"/api/v1/accounts/{account_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == account_id

    @pytest.mark.asyncio
    async def test_update_account(self, client: AsyncClient) -> None:
        # Create first
        resp = await client.post(
            "/api/v1/accounts/",
            json={"name": "Old", "type": "cash"},
        )
        account_id = resp.json()["id"]

        # Update
        resp = await client.put(
            f"/api/v1/accounts/{account_id}",
            json={"name": "New Name", "currency": "USD"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "New Name"
        assert body["currency"] == "USD"

    @pytest.mark.asyncio
    async def test_delete_account(self, client: AsyncClient) -> None:
        # Create
        resp = await client.post(
            "/api/v1/accounts/",
            json={"name": "Temp", "type": "paypal"},
        )
        account_id = resp.json()["id"]

        # Delete (soft)
        resp = await client.delete(f"/api/v1/accounts/{account_id}")
        assert resp.status_code == 204

        # Should no longer appear in list (list returns active only)
        resp = await client.get("/api/v1/accounts/")
        assert all(a["id"] != account_id for a in resp.json()["items"])

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_404(self, client: AsyncClient) -> None:
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/accounts/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_data_isolation(self, client: AsyncClient) -> None:
        """Accounts created by user A must not be visible to user B."""
        # Create as default mock user (user A)
        resp = await client.post(
            "/api/v1/accounts/",
            json={"name": "User A account", "type": "bank"},
        )
        account_id = resp.json()["id"]

        # Switch to user B
        app.dependency_overrides[get_current_user] = lambda: _make_mock_user(OTHER_USER_ID)

        resp = await client.get(f"/api/v1/accounts/{account_id}")
        assert resp.status_code == 404

        resp = await client.get("/api/v1/accounts/")
        assert resp.json()["total"] == 0

        # Restore user A for subsequent tests
        app.dependency_overrides[get_current_user] = lambda: _make_mock_user()

    @pytest.mark.asyncio
    async def test_create_with_optional_fields(self, client: AsyncClient) -> None:
        payload = {
            "name": "Savings",
            "type": "bank",
            "currency": "GBP",
            "color": "#FF5733",
            "icon": "piggy-bank",
        }
        resp = await client.post("/api/v1/accounts/", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["currency"] == "GBP"
        assert body["color"] == "#FF5733"
        assert body["icon"] == "piggy-bank"

    @pytest.mark.asyncio
    async def test_create_invalid_payload(self, client: AsyncClient) -> None:
        resp = await client.post("/api/v1/accounts/", json={"type": "bank"})
        assert resp.status_code == 422  # missing required 'name'

    @pytest.mark.asyncio
    async def test_list_after_multiple_creates(self, client: AsyncClient) -> None:
        for name in ("A", "B", "C"):
            await client.post("/api/v1/accounts/", json={"name": name, "type": "cash"})
        resp = await client.get("/api/v1/accounts/")
        assert resp.json()["total"] == 3
