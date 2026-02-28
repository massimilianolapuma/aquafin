"""Tests for the Export API (CSV, JSON, GDPR)."""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.account import Account, AccountType
from app.models.categorization_rule import CategorizationRule, MatchType
from app.models.category import Category
from app.models.import_record import (
    FileType,
    ImportRecord,
    ImportStatus,
    SourceType,
)
from app.models.transaction import CategorizationMethod, Transaction, TransactionType
from app.models.user import User
from app.schemas.export import ExportFilters, GdprExportResponse, TransactionExportRow

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MOCK_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
MOCK_ACCOUNT_ID = uuid.UUID("00000000-0000-4000-8000-aaa000000001")
MOCK_CATEGORY_ID = uuid.UUID("00000000-0000-4000-8000-ccc000000001")
MOCK_TXN_ID = uuid.UUID("00000000-0000-4000-8000-ddd000000001")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(user_id: uuid.UUID = MOCK_USER_ID) -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=user_id,
        clerk_id=f"clerk_{user_id.hex[:8]}",
        email=f"{user_id.hex[:8]}@test.com",
        display_name="Test User",
        locale="it",
        preferences={},
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def _mock_get_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture(autouse=True)
def _restore_overrides():
    """Save and restore app.dependency_overrides so tests don't leak state."""
    saved = dict(app.dependency_overrides)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestExportSchemas:
    """Tests for export Pydantic schemas."""

    def test_export_filters_defaults(self) -> None:
        """All filter fields default to None."""
        f = ExportFilters()
        assert f.account_id is None
        assert f.category_id is None
        assert f.date_from is None
        assert f.date_to is None
        assert f.type is None

    def test_export_filters_with_values(self) -> None:
        """Filters accept explicit values."""
        f = ExportFilters(
            account_id=MOCK_ACCOUNT_ID,
            category_id=MOCK_CATEGORY_ID,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 12, 31),
            type="expense",
        )
        assert f.account_id == MOCK_ACCOUNT_ID
        assert f.date_from == date(2025, 1, 1)
        assert f.type == "expense"

    def test_transaction_export_row_from_attributes(self) -> None:
        """TransactionExportRow can be built from keyword args."""
        row = TransactionExportRow(
            date=date(2025, 3, 1),
            description="Test",
            amount=Decimal("42.50"),
            currency="EUR",
            type="expense",
            category_name="Food",
            account_name="Main",
            categorization_method="manual",
        )
        assert row.amount == Decimal("42.50")
        assert row.account_name == "Main"

    def test_gdpr_export_response_structure(self) -> None:
        """GdprExportResponse validates required top-level keys."""
        data = GdprExportResponse(
            user={"id": "u1"},
            accounts=[],
            categories=[],
            transactions=[],
            imports=[],
            rules=[],
            exported_at=datetime.now(timezone.utc),
        )
        assert data.user == {"id": "u1"}
        assert isinstance(data.exported_at, datetime)


# ---------------------------------------------------------------------------
# Service-level tests (mock DB)
# ---------------------------------------------------------------------------


class TestExportServiceCsv:
    """Service-layer tests for CSV export."""

    @pytest.mark.anyio
    async def test_csv_header_row(self) -> None:
        """CSV output starts with the expected Italian header."""
        with patch(
            "app.services.export_service._query_transactions",
            return_value=[],
        ):
            from app.services.export_service import export_transactions_csv

            result = await export_transactions_csv(
                AsyncMock(), MOCK_USER_ID, ExportFilters()
            )
        reader = csv.reader(io.StringIO(result), delimiter=";")
        header = next(reader)
        assert header == [
            "Data",
            "Descrizione",
            "Importo",
            "Valuta",
            "Tipo",
            "Categoria",
            "Conto",
            "Metodo categorizzazione",
        ]

    @pytest.mark.anyio
    async def test_csv_data_rows(self) -> None:
        """CSV contains the correct data for each transaction row."""
        rows = [
            TransactionExportRow(
                date=date(2025, 3, 1),
                description="ESSELUNGA",
                amount=Decimal("-45.80"),
                currency="EUR",
                type="expense",
                category_name="Supermercato",
                account_name="Conto Corrente",
                categorization_method="keyword",
            ),
        ]
        with patch(
            "app.services.export_service._query_transactions",
            return_value=rows,
        ):
            from app.services.export_service import export_transactions_csv

            result = await export_transactions_csv(
                AsyncMock(), MOCK_USER_ID, ExportFilters()
            )
        reader = csv.reader(io.StringIO(result), delimiter=";")
        next(reader)  # skip header
        data = next(reader)
        assert data[0] == "2025-03-01"
        assert data[1] == "ESSELUNGA"
        assert data[2] == "-45.80"
        assert data[5] == "Supermercato"

    @pytest.mark.anyio
    async def test_csv_empty_export(self) -> None:
        """Empty result set yields header-only CSV."""
        with patch(
            "app.services.export_service._query_transactions",
            return_value=[],
        ):
            from app.services.export_service import export_transactions_csv

            result = await export_transactions_csv(
                AsyncMock(), MOCK_USER_ID, ExportFilters()
            )
        lines = result.strip().split("\n")
        assert len(lines) == 1  # header only


class TestExportServiceJson:
    """Service-layer tests for JSON export."""

    @pytest.mark.anyio
    async def test_json_returns_list(self) -> None:
        """JSON export returns a list of dicts."""
        rows = [
            TransactionExportRow(
                date=date(2025, 3, 1),
                description="Test",
                amount=Decimal("100.00"),
                currency="EUR",
                type="income",
                category_name="Salary",
                account_name="Main",
                categorization_method="manual",
            ),
        ]
        with patch(
            "app.services.export_service._query_transactions",
            return_value=rows,
        ):
            from app.services.export_service import export_transactions_json

            result = await export_transactions_json(
                AsyncMock(), MOCK_USER_ID, ExportFilters()
            )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["amount"] == "100.00"
        assert result[0]["type"] == "income"

    @pytest.mark.anyio
    async def test_json_empty_export(self) -> None:
        """Empty result set returns empty list."""
        with patch(
            "app.services.export_service._query_transactions",
            return_value=[],
        ):
            from app.services.export_service import export_transactions_json

            result = await export_transactions_json(
                AsyncMock(), MOCK_USER_ID, ExportFilters()
            )
        assert result == []


class TestExportServiceGdpr:
    """Service-layer tests for GDPR export."""

    @pytest.mark.anyio
    async def test_gdpr_structure(self) -> None:
        """GDPR export contains all expected top-level keys."""
        mock_db = AsyncMock()
        # User query
        mock_user_row = MagicMock()
        mock_user_row.scalar_one_or_none.return_value = _make_mock_user()
        # Other queries return empty scalars
        mock_empty = MagicMock()
        mock_empty.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(
            side_effect=[mock_user_row, mock_empty, mock_empty, mock_empty, mock_empty, mock_empty]
        )

        from app.services.export_service import export_gdpr

        result = await export_gdpr(mock_db, MOCK_USER_ID)

        assert "user" in result
        assert "accounts" in result
        assert "categories" in result
        assert "transactions" in result
        assert "imports" in result
        assert "rules" in result
        assert "exported_at" in result

    @pytest.mark.anyio
    async def test_gdpr_user_fields(self) -> None:
        """GDPR user section contains expected fields."""
        mock_db = AsyncMock()
        mock_user_row = MagicMock()
        mock_user_row.scalar_one_or_none.return_value = _make_mock_user()
        mock_empty = MagicMock()
        mock_empty.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(
            side_effect=[mock_user_row, mock_empty, mock_empty, mock_empty, mock_empty, mock_empty]
        )

        from app.services.export_service import export_gdpr

        result = await export_gdpr(mock_db, MOCK_USER_ID)
        user = result["user"]
        assert user["email"] == f"{MOCK_USER_ID.hex[:8]}@test.com"
        assert user["locale"] == "it"
        assert "id" in user
        assert "clerk_id" in user


# ---------------------------------------------------------------------------
# API endpoint tests (HTTP-level)
# ---------------------------------------------------------------------------


class TestExportCsvEndpoint:
    """HTTP-level tests for GET /api/v1/exports/csv."""

    @pytest.mark.anyio
    async def test_csv_returns_200(self) -> None:
        """CSV endpoint returns 200 with text/csv content type."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_transactions_csv",
            return_value="Data;Descrizione\n2025-03-01;Test\n",
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/exports/csv")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers["content-type"]

    @pytest.mark.anyio
    async def test_csv_content_disposition(self) -> None:
        """CSV response includes Content-Disposition attachment header."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_transactions_csv",
            return_value="header\n",
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/exports/csv")
        assert "attachment" in resp.headers.get("content-disposition", "")
        assert "aquafin_export_" in resp.headers.get("content-disposition", "")

    @pytest.mark.anyio
    async def test_csv_utf8_bom(self) -> None:
        """CSV body starts with UTF-8 BOM bytes for Excel compatibility."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_transactions_csv",
            return_value="Data;Descrizione\n",
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/exports/csv")
        # UTF-8 BOM is \xef\xbb\xbf
        assert resp.content[:3] == b"\xef\xbb\xbf"


class TestExportJsonEndpoint:
    """HTTP-level tests for GET /api/v1/exports/json."""

    @pytest.mark.anyio
    async def test_json_returns_200(self) -> None:
        """JSON endpoint returns 200 with application/json."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_transactions_json",
            return_value=[{"date": "2025-03-01", "amount": "42.50"}],
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/exports/json")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1

    @pytest.mark.anyio
    async def test_json_with_filters(self) -> None:
        """JSON endpoint accepts query-string filters."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_transactions_json",
            return_value=[],
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get(
                    "/api/v1/exports/json",
                    params={
                        "account_id": str(MOCK_ACCOUNT_ID),
                        "date_from": "2025-01-01",
                        "date_to": "2025-12-31",
                        "type": "expense",
                    },
                )
        assert resp.status_code == 200

    @pytest.mark.anyio
    async def test_json_empty(self) -> None:
        """JSON endpoint returns empty list when no transactions match."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_transactions_json",
            return_value=[],
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/exports/json")
        assert resp.json() == []


class TestExportGdprEndpoint:
    """HTTP-level tests for GET /api/v1/exports/gdpr."""

    @pytest.mark.anyio
    async def test_gdpr_returns_200(self) -> None:
        """GDPR endpoint returns 200."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_gdpr",
            return_value={
                "user": {"id": str(MOCK_USER_ID)},
                "accounts": [],
                "categories": [],
                "transactions": [],
                "imports": [],
                "rules": [],
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/exports/gdpr")
        assert resp.status_code == 200
        data = resp.json()
        assert "user" in data
        assert "exported_at" in data

    @pytest.mark.anyio
    async def test_gdpr_contains_all_sections(self) -> None:
        """GDPR response has all required top-level keys."""
        mock_user = _make_mock_user()
        app.dependency_overrides[get_current_user] = lambda: mock_user
        app.dependency_overrides[get_db] = _mock_get_db
        with patch(
            "app.services.export_service.export_gdpr",
            return_value={
                "user": {"id": str(MOCK_USER_ID), "email": "test@test.com"},
                "accounts": [{"id": "a1"}],
                "categories": [{"id": "c1"}],
                "transactions": [{"id": "t1"}],
                "imports": [{"id": "i1"}],
                "rules": [{"id": "r1"}],
                "exported_at": datetime.now(timezone.utc).isoformat(),
            },
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.get("/api/v1/exports/gdpr")
        data = resp.json()
        for key in ("user", "accounts", "categories", "transactions", "imports", "rules"):
            assert key in data


class TestExportUnauthorized:
    """Verify that unauthenticated requests are rejected."""

    @pytest.mark.anyio
    async def test_csv_unauthorized(self) -> None:
        """CSV endpoint rejects requests without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/exports/csv")
        # 401/403 if auth raises HTTPException, 422 if token validation fails
        assert resp.status_code in (401, 403, 422)

    @pytest.mark.anyio
    async def test_json_unauthorized(self) -> None:
        """JSON endpoint rejects requests without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/exports/json")
        assert resp.status_code in (401, 403, 422)

    @pytest.mark.anyio
    async def test_gdpr_unauthorized(self) -> None:
        """GDPR endpoint rejects requests without auth."""
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/exports/gdpr")
        assert resp.status_code in (401, 403, 422)
