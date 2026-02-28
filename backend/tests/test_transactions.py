"""Tests for the Transactions CRUD API."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.account import Account, AccountType
from app.models.base import Base
from app.models.transaction import CategorizationMethod, Transaction, TransactionType
from app.models.user import User
from app.schemas.transaction import (
    BulkCategorizeRequest,
    RecategorizeRequest,
    TransactionListParams,
    TransactionRead,
    TransactionUpdate,
)

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

MOCK_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000011")
OTHER_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000012")
MOCK_ACCOUNT_ID = uuid.UUID("00000000-0000-4000-8000-000000000021")
OTHER_ACCOUNT_ID = uuid.UUID("00000000-0000-4000-8000-000000000022")
MOCK_CATEGORY_ID = uuid.UUID("00000000-0000-4000-8000-000000000031")


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


async def _seed_account(
    session: AsyncSession,
    user_id: uuid.UUID = MOCK_USER_ID,
    account_id: uuid.UUID = MOCK_ACCOUNT_ID,
) -> Account:
    """Create a test account."""
    account = Account(
        id=account_id,
        user_id=user_id,
        name="Test Bank",
        type=AccountType.bank,
        currency="EUR",
        is_active=True,
    )
    session.add(account)
    await session.flush()
    return account


async def _seed_transaction(
    session: AsyncSession,
    account_id: uuid.UUID = MOCK_ACCOUNT_ID,
    *,
    amount: Decimal = Decimal("100.00"),
    tx_date: date | None = None,
    description: str = "Test Transaction",
    original_description: str | None = None,
    tx_type: TransactionType = TransactionType.expense,
    category_id: uuid.UUID | None = None,
    transaction_id: uuid.UUID | None = None,
) -> Transaction:
    """Create a test transaction."""
    tx = Transaction(
        id=transaction_id or uuid.uuid4(),
        account_id=account_id,
        amount=amount,
        currency="EUR",
        date=tx_date or date(2025, 6, 15),
        description=description,
        original_description=original_description or description,
        type=tx_type,
        categorization_method=CategorizationMethod.uncategorized,
        is_recurring=False,
        tags=[],
        metadata_extra={},
        category_id=category_id,
    )
    session.add(tx)
    await session.flush()
    return tx


async def _seed_user(session: AsyncSession, user_id: uuid.UUID = MOCK_USER_ID) -> User:
    """Create a test user in the DB."""
    user = User(
        id=user_id,
        clerk_id=f"clerk_{user_id.hex[:8]}",
        email=f"{user_id.hex[:8]}@test.com",
        display_name="Test User",
        locale="en",
        preferences={},
        is_active=True,
    )
    session.add(user)
    await session.flush()
    return user


@pytest.fixture
async def seeded_db() -> AsyncSession:  # type: ignore[misc]
    """Provide a DB session with a user, account, and some transactions."""
    async with _TestSession() as session:
        await _seed_user(session)
        await _seed_account(session)
        await _seed_transaction(
            session, description="Grocery Store", original_description="GROCERY STORE #123"
        )
        await _seed_transaction(
            session,
            description="Electric Bill",
            tx_type=TransactionType.income,
            amount=Decimal("250.00"),
        )
        await _seed_transaction(session, description="Coffee Shop", tx_date=date(2025, 5, 1))
        await session.commit()
        yield session  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestTransactionSchemas:
    """Pydantic schema edge-case validation."""

    def test_transaction_update_all_none(self) -> None:
        """All fields optional – empty update should be valid."""
        data = TransactionUpdate()
        assert data.category_id is None
        assert data.description is None
        assert data.tags is None
        assert data.is_recurring is None

    def test_transaction_update_partial(self) -> None:
        data = TransactionUpdate(description="Updated")
        assert data.description == "Updated"
        assert data.tags is None

    def test_transaction_update_with_tags(self) -> None:
        data = TransactionUpdate(tags=["food", "groceries"])
        assert data.tags == ["food", "groceries"]

    def test_transaction_list_params_defaults(self) -> None:
        params = TransactionListParams()
        assert params.page == 1
        assert params.limit == 20
        assert params.account_id is None

    def test_transaction_list_params_page_ge_1(self) -> None:
        with pytest.raises(ValidationError):
            TransactionListParams(page=0)

    def test_transaction_list_params_limit_le_100(self) -> None:
        with pytest.raises(ValidationError):
            TransactionListParams(limit=101)

    def test_transaction_list_params_limit_ge_1(self) -> None:
        with pytest.raises(ValidationError):
            TransactionListParams(limit=0)

    def test_recategorize_request_valid(self) -> None:
        req = RecategorizeRequest(category_id=MOCK_CATEGORY_ID)
        assert req.apply_to_similar is False

    def test_recategorize_request_with_similar(self) -> None:
        req = RecategorizeRequest(category_id=MOCK_CATEGORY_ID, apply_to_similar=True)
        assert req.apply_to_similar is True

    def test_bulk_categorize_request_valid(self) -> None:
        req = BulkCategorizeRequest(
            transaction_ids=[uuid.uuid4(), uuid.uuid4()],
            category_id=MOCK_CATEGORY_ID,
        )
        assert len(req.transaction_ids) == 2

    def test_bulk_categorize_request_empty_list(self) -> None:
        req = BulkCategorizeRequest(
            transaction_ids=[],
            category_id=MOCK_CATEGORY_ID,
        )
        assert len(req.transaction_ids) == 0

    def test_transaction_read_from_attributes(self) -> None:
        """TransactionRead should have from_attributes=True."""
        assert TransactionRead.model_config.get("from_attributes") is True


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


class TestTransactionService:
    """Tests for transaction_service functions using real SQLite."""

    @pytest.mark.asyncio
    async def test_list_transactions_empty(self) -> None:
        """Listing with no transactions returns empty."""
        from app.services import transaction_service

        async with _TestSession() as session:
            await _seed_user(session)
            await _seed_account(session)
            await session.commit()

            params = TransactionListParams()
            items, total = await transaction_service.list_transactions(
                session, MOCK_USER_ID, params
            )
            assert items == []
            assert total == 0

    @pytest.mark.asyncio
    async def test_list_transactions_with_data(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams()
        items, total = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        assert total == 3
        assert len(items) == 3

    @pytest.mark.asyncio
    async def test_list_transactions_filter_by_type(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams(type="income")
        items, total = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        assert total == 1
        assert items[0].description == "Electric Bill"

    @pytest.mark.asyncio
    async def test_list_transactions_search(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams(search="coffee")
        items, total = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        assert total == 1
        assert "Coffee" in items[0].description

    @pytest.mark.asyncio
    async def test_list_transactions_date_filter(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams(date_from=date(2025, 6, 1), date_to=date(2025, 6, 30))
        items, total = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        assert total == 2  # Two transactions are in June

    @pytest.mark.asyncio
    async def test_list_transactions_pagination(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams(page=1, limit=2)
        items, total = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        assert total == 3
        assert len(items) == 2

        params2 = TransactionListParams(page=2, limit=2)
        items2, total2 = await transaction_service.list_transactions(
            seeded_db, MOCK_USER_ID, params2
        )
        assert total2 == 3
        assert len(items2) == 1

    @pytest.mark.asyncio
    async def test_get_transaction_found(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams()
        items, _ = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        tx_id = items[0].id

        tx = await transaction_service.get_transaction(seeded_db, MOCK_USER_ID, tx_id)
        assert tx.id == tx_id

    @pytest.mark.asyncio
    async def test_get_transaction_not_found(self) -> None:
        from app.services import transaction_service

        async with _TestSession() as session:
            await _seed_user(session)
            await _seed_account(session)
            await session.commit()

            with pytest.raises(Exception) as exc_info:
                await transaction_service.get_transaction(session, MOCK_USER_ID, uuid.uuid4())
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_transaction_wrong_user(self) -> None:
        """Transaction belongs to another user → 404."""
        from app.services import transaction_service

        async with _TestSession() as session:
            await _seed_user(session, MOCK_USER_ID)
            await _seed_user(session, OTHER_USER_ID)
            await _seed_account(session, MOCK_USER_ID, MOCK_ACCOUNT_ID)
            tx = await _seed_transaction(session, MOCK_ACCOUNT_ID)
            await session.commit()

            with pytest.raises(Exception) as exc_info:
                await transaction_service.get_transaction(session, OTHER_USER_ID, tx.id)
            assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_update_transaction(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams()
        items, _ = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        tx_id = items[0].id

        updated = await transaction_service.update_transaction(
            seeded_db, MOCK_USER_ID, tx_id, TransactionUpdate(description="Updated Desc")
        )
        assert updated.description == "Updated Desc"

    @pytest.mark.asyncio
    async def test_delete_transaction(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams()
        items, _ = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        tx_id = items[0].id

        await transaction_service.delete_transaction(seeded_db, MOCK_USER_ID, tx_id)

        with pytest.raises(Exception) as exc_info:
            await transaction_service.get_transaction(seeded_db, MOCK_USER_ID, tx_id)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_bulk_categorize(self) -> None:
        from app.services import transaction_service

        async with _TestSession() as session:
            await _seed_user(session)
            await _seed_account(session)
            tx1 = await _seed_transaction(session, description="Tx 1")
            tx2 = await _seed_transaction(session, description="Tx 2")
            await session.commit()

            count = await transaction_service.bulk_categorize(
                session, MOCK_USER_ID, [tx1.id, tx2.id], MOCK_CATEGORY_ID
            )
            assert count == 2

    @pytest.mark.asyncio
    async def test_bulk_categorize_empty(self) -> None:
        from app.services import transaction_service

        async with _TestSession() as session:
            count = await transaction_service.bulk_categorize(
                session, MOCK_USER_ID, [], MOCK_CATEGORY_ID
            )
            assert count == 0

    @pytest.mark.asyncio
    async def test_recategorize_single(self, seeded_db: AsyncSession) -> None:
        from app.services import transaction_service

        params = TransactionListParams()
        items, _ = await transaction_service.list_transactions(seeded_db, MOCK_USER_ID, params)
        tx_id = items[0].id

        result = await transaction_service.recategorize(
            seeded_db, MOCK_USER_ID, tx_id, MOCK_CATEGORY_ID, apply_to_similar=False
        )
        assert result.category_id == MOCK_CATEGORY_ID
        assert result.categorization_method == CategorizationMethod.manual

    @pytest.mark.asyncio
    async def test_recategorize_apply_to_similar(self) -> None:
        from app.services import transaction_service

        async with _TestSession() as session:
            await _seed_user(session)
            await _seed_account(session)
            tx1 = await _seed_transaction(
                session, description="Supermarket", original_description="SUPERMARKET #42"
            )
            tx2 = await _seed_transaction(
                session, description="Supermarket 2", original_description="SUPERMARKET #42"
            )
            tx3 = await _seed_transaction(
                session, description="Coffee", original_description="COFFEE SHOP"
            )
            await session.commit()

            result = await transaction_service.recategorize(
                session, MOCK_USER_ID, tx1.id, MOCK_CATEGORY_ID, apply_to_similar=True
            )
            assert result.category_id == MOCK_CATEGORY_ID

            # tx2 should also be updated (same original_description)
            await session.refresh(tx2)
            assert tx2.category_id == MOCK_CATEGORY_ID

            # tx3 should NOT be updated (different original_description)
            await session.refresh(tx3)
            assert tx3.category_id is None

    @pytest.mark.asyncio
    async def test_list_transactions_filter_by_account(self) -> None:
        from app.services import transaction_service

        other_account_id = uuid.uuid4()
        async with _TestSession() as session:
            await _seed_user(session)
            await _seed_account(session, MOCK_USER_ID, MOCK_ACCOUNT_ID)
            await _seed_account(session, MOCK_USER_ID, other_account_id)
            await _seed_transaction(session, MOCK_ACCOUNT_ID, description="Tx A")
            await _seed_transaction(session, other_account_id, description="Tx B")
            await session.commit()

            params = TransactionListParams(account_id=MOCK_ACCOUNT_ID)
            items, total = await transaction_service.list_transactions(
                session, MOCK_USER_ID, params
            )
            assert total == 1
            assert items[0].description == "Tx A"


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------


class TestTransactionsAPI:
    """End-to-end tests via the HTTP API."""

    @pytest.fixture(autouse=True)
    async def _seed_for_api(self) -> None:  # type: ignore[misc]
        """Seed the DB with test data before each API test."""
        async with _TestSession() as session:
            await _seed_user(session)
            await _seed_account(session)
            await session.commit()
        yield  # type: ignore[misc]

    @pytest.mark.asyncio
    async def test_list_empty(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/transactions/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["page"] == 1
        assert body["limit"] == 20

    @pytest.mark.asyncio
    async def test_list_with_transactions(self, client: AsyncClient) -> None:
        # Seed transactions
        async with _TestSession() as session:
            await _seed_transaction(session, description="API Tx 1")
            await _seed_transaction(session, description="API Tx 2")
            await session.commit()

        resp = await client.get("/api/v1/transactions/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_transaction(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            tx = await _seed_transaction(session, description="Get Me")
            await session.commit()
            tx_id = tx.id

        resp = await client.get(f"/api/v1/transactions/{tx_id}")
        assert resp.status_code == 200
        assert resp.json()["description"] == "Get Me"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_404(self, client: AsyncClient) -> None:
        fake_id = uuid.uuid4()
        resp = await client.get(f"/api/v1/transactions/{fake_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_transaction(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            tx = await _seed_transaction(session, description="Old Name")
            await session.commit()
            tx_id = tx.id

        resp = await client.put(
            f"/api/v1/transactions/{tx_id}",
            json={"description": "New Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "New Name"

    @pytest.mark.asyncio
    async def test_delete_transaction(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            tx = await _seed_transaction(session, description="Delete Me")
            await session.commit()
            tx_id = tx.id

        resp = await client.delete(f"/api/v1/transactions/{tx_id}")
        assert resp.status_code == 204

        # Verify deleted
        resp = await client.get(f"/api/v1/transactions/{tx_id}")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_recategorize(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            tx = await _seed_transaction(session, description="Recat Me")
            await session.commit()
            tx_id = tx.id

        resp = await client.post(
            f"/api/v1/transactions/{tx_id}/recategorize",
            json={"category_id": str(MOCK_CATEGORY_ID)},
        )
        assert resp.status_code == 200
        assert resp.json()["category_id"] == str(MOCK_CATEGORY_ID)

    @pytest.mark.asyncio
    async def test_bulk_categorize(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            tx1 = await _seed_transaction(session, description="Bulk 1")
            tx2 = await _seed_transaction(session, description="Bulk 2")
            await session.commit()

        resp = await client.post(
            "/api/v1/transactions/bulk-categorize",
            json={
                "transaction_ids": [str(tx1.id), str(tx2.id)],
                "category_id": str(MOCK_CATEGORY_ID),
            },
        )
        assert resp.status_code == 200
        assert resp.json()["updated_count"] == 2

    @pytest.mark.asyncio
    async def test_list_with_search(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            await _seed_transaction(session, description="Unique Pizza Place")
            await _seed_transaction(session, description="Other Store")
            await session.commit()

        resp = await client.get("/api/v1/transactions/", params={"search": "pizza"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert "Pizza" in body["items"][0]["description"]

    @pytest.mark.asyncio
    async def test_list_with_pagination(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            for i in range(5):
                await _seed_transaction(session, description=f"Paginated {i}")
            await session.commit()

        resp = await client.get("/api/v1/transactions/", params={"page": 1, "limit": 2})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 5
        assert len(body["items"]) == 2
        assert body["page"] == 1
        assert body["limit"] == 2

    @pytest.mark.asyncio
    async def test_list_with_date_filter(self, client: AsyncClient) -> None:
        async with _TestSession() as session:
            await _seed_transaction(session, description="Jan Tx", tx_date=date(2025, 1, 15))
            await _seed_transaction(session, description="Jul Tx", tx_date=date(2025, 7, 15))
            await session.commit()

        resp = await client.get(
            "/api/v1/transactions/",
            params={"date_from": "2025-07-01", "date_to": "2025-07-31"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["items"][0]["description"] == "Jul Tx"

    @pytest.mark.asyncio
    async def test_data_isolation(self, client: AsyncClient) -> None:
        """Transactions of user A must not be visible to user B."""
        async with _TestSession() as session:
            tx = await _seed_transaction(session, description="User A Tx")
            await session.commit()
            tx_id = tx.id

        # Switch to user B
        app.dependency_overrides[get_current_user] = lambda: _make_mock_user(OTHER_USER_ID)

        resp = await client.get(f"/api/v1/transactions/{tx_id}")
        assert resp.status_code == 404

        resp = await client.get("/api/v1/transactions/")
        assert resp.json()["total"] == 0

        # Restore user A for subsequent tests
        app.dependency_overrides[get_current_user] = lambda: _make_mock_user()

    @pytest.mark.asyncio
    async def test_update_nonexistent_returns_404(self, client: AsyncClient) -> None:
        fake_id = uuid.uuid4()
        resp = await client.put(
            f"/api/v1/transactions/{fake_id}",
            json={"description": "Nope"},
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_404(self, client: AsyncClient) -> None:
        fake_id = uuid.uuid4()
        resp = await client.delete(f"/api/v1/transactions/{fake_id}")
        assert resp.status_code == 404
