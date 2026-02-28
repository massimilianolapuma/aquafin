"""Tests for the Import upload → preview → confirm workflow."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.auth import get_current_user
from app.core.database import get_db
from app.main import app
from app.models.import_record import FileType, ImportRecord, ImportStatus, SourceType
from app.models.user import User
from app.schemas.import_record import (
    ImportConfirmRequest,
    ImportConfirmResponse,
    ImportListItem,
    ImportListResponse,
    ImportPreviewResponse,
    ImportUploadResponse,
    TransactionPreview,
)
from app.services.categorization.models import CategorizationResult, CategorizedTransaction
from app.services.parser.base import ParseResult, RawTransaction

# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

MOCK_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
OTHER_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000002")
MOCK_ACCOUNT_ID = uuid.UUID("00000000-0000-4000-8000-aaa000000001")
MOCK_IMPORT_ID = uuid.UUID("00000000-0000-4000-8000-bbb000000001")

BANK_CSV_CONTENT = (
    b"Data Operazione;Data Valuta;Descrizione;Importo\n"
    b"01/03/2025;01/03/2025;PAGAMENTO POS ESSELUNGA VIA ROMA MI;-45,80\n"
    b"03/03/2025;03/03/2025;BONIFICO DA AZIENDA SRL - STIPENDIO MARZO 2025;2.350,00\n"
    b"05/03/2025;07/03/2025;ADDEBITO SDD ENEL ENERGIA SPA;-89,50\n"
    b"10/03/2025;10/03/2025;PRELIEVO BANCOMAT ATM 12345;-200,00\n"
    b"15/03/2025;15/03/2025;POS AMAZON EU S.A.R.L.;-32,99\n"
    b"20/03/2025;20/03/2025;GIROCONTO DA CONTO DEPOSITO;500,00\n"
)


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


def _make_import_record(
    import_id: uuid.UUID = MOCK_IMPORT_ID,
    user_id: uuid.UUID = MOCK_USER_ID,
    account_id: uuid.UUID = MOCK_ACCOUNT_ID,
    status: ImportStatus = ImportStatus.preview,
    row_count: int = 6,
    imported_count: int = 0,
) -> ImportRecord:
    """Create a mock ImportRecord."""
    now = datetime.now(UTC)
    return ImportRecord(
        id=import_id,
        account_id=account_id,
        user_id=user_id,
        filename="bank_sample.csv",
        file_type=FileType.csv,
        source_type=SourceType.bank_csv,
        status=status,
        row_count=row_count,
        imported_count=imported_count,
        error_log=[],
        created_at=now,
        updated_at=now,
    )


def _make_categorized_transactions() -> list[CategorizedTransaction]:
    """Create sample categorized transactions."""
    return [
        CategorizedTransaction(
            date=date(2025, 3, 1),
            amount=Decimal("-45.80"),
            currency="EUR",
            description="PAGAMENTO POS ESSELUNGA VIA ROMA MI",
            original_description="PAGAMENTO POS ESSELUNGA VIA ROMA MI",
            type="expense",
            metadata={},
            categorization=CategorizationResult(
                category_name="Supermercato",
                confidence=0.7,
                matched_by="keyword",
            ),
        ),
        CategorizedTransaction(
            date=date(2025, 3, 3),
            amount=Decimal("2350.00"),
            currency="EUR",
            description="BONIFICO DA AZIENDA SRL - STIPENDIO MARZO 2025",
            original_description="BONIFICO DA AZIENDA SRL - STIPENDIO MARZO 2025",
            type="income",
            metadata={},
            categorization=CategorizationResult(
                category_name="Stipendio",
                confidence=0.7,
                matched_by="keyword",
            ),
        ),
        CategorizedTransaction(
            date=date(2025, 3, 5),
            amount=Decimal("-89.50"),
            currency="EUR",
            description="ADDEBITO SDD ENEL ENERGIA SPA",
            original_description="ADDEBITO SDD ENEL ENERGIA SPA",
            type="expense",
            metadata={},
            categorization=CategorizationResult(
                category_name="Utenze",
                confidence=0.7,
                matched_by="keyword",
            ),
        ),
    ]


# ---- Mock DB session (no real DB needed – service layer is mocked) ----

from unittest.mock import AsyncMock as _AM

from sqlalchemy.ext.asyncio import AsyncSession


def _mock_get_db() -> AsyncSession:  # type: ignore[misc]
    """Return a no-op mock session. Service calls are patched individually."""
    yield _AM(spec=AsyncSession)  # type: ignore[misc]


# Apply dependency overrides
app.dependency_overrides[get_current_user] = lambda: _make_mock_user()
app.dependency_overrides[get_db] = _mock_get_db


@pytest.fixture
async def client() -> AsyncClient:  # type: ignore[misc]
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------


class TestImportSchemas:
    """Pydantic schema validation tests."""

    def test_upload_response_from_attributes(self) -> None:
        """ImportUploadResponse can be built from an ImportRecord instance."""
        record = _make_import_record()
        resp = ImportUploadResponse.model_validate(record)
        assert resp.filename == "bank_sample.csv"
        assert resp.status == ImportStatus.preview

    def test_transaction_preview(self) -> None:
        """TransactionPreview accepts valid data."""
        tp = TransactionPreview(
            temp_id=0,
            date=date(2025, 3, 1),
            amount=-45.80,
            currency="EUR",
            description="ESSELUNGA",
            original_description="PAGAMENTO POS ESSELUNGA",
            type="expense",
            category_name="Supermercato",
            confidence=0.7,
            matched_by="keyword",
        )
        assert tp.temp_id == 0
        assert tp.amount == -45.80

    def test_confirm_request_defaults(self) -> None:
        """ImportConfirmRequest defaults to empty overrides."""
        req = ImportConfirmRequest()
        assert req.category_overrides == {}

    def test_confirm_request_with_overrides(self) -> None:
        """ImportConfirmRequest accepts category_overrides."""
        req = ImportConfirmRequest(category_overrides={0: "Alimentari", 2: "Bollette"})
        assert req.category_overrides[0] == "Alimentari"

    def test_confirm_response(self) -> None:
        """ImportConfirmResponse accepts valid data."""
        resp = ImportConfirmResponse(
            import_id=MOCK_IMPORT_ID,
            status=ImportStatus.confirmed,
            imported_count=6,
            categorized_count=4,
        )
        assert resp.imported_count == 6

    def test_list_item_from_attributes(self) -> None:
        """ImportListItem can be built from an ImportRecord instance."""
        record = _make_import_record()
        item = ImportListItem.model_validate(record)
        assert item.file_type == FileType.csv

    def test_list_response(self) -> None:
        """ImportListResponse with items."""
        record = _make_import_record()
        item = ImportListItem.model_validate(record)
        resp = ImportListResponse(items=[item], total=1)
        assert resp.total == 1

    def test_preview_response(self) -> None:
        """ImportPreviewResponse with transactions."""
        tp = TransactionPreview(
            temp_id=0,
            date=date(2025, 3, 1),
            amount=-45.80,
            currency="EUR",
            description="test",
            original_description="test",
            type="expense",
        )
        resp = ImportPreviewResponse(
            import_id=MOCK_IMPORT_ID,
            filename="test.csv",
            source_type=SourceType.bank_csv,
            status=ImportStatus.preview,
            row_count=1,
            transactions=[tp],
        )
        assert len(resp.transactions) == 1


# ---------------------------------------------------------------------------
# Service-level tests (mocked DB)
# ---------------------------------------------------------------------------


class TestImportServiceUnit:
    """Unit tests for import_service functions with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_upload_and_parse_calls_parser(self) -> None:
        """upload_and_parse invokes ParserRegistry and CategorizationEngine."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.flush = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda obj: None)

        raw_txs = [
            RawTransaction(
                date=date(2025, 3, 1),
                amount=Decimal("-45.80"),
                currency="EUR",
                description="ESSELUNGA",
                original_description="ESSELUNGA",
                type="expense",
            )
        ]
        parse_result = ParseResult(
            transactions=raw_txs,
            source_type="bank_csv",
            row_count=1,
            parsed_count=1,
            errors=[],
        )

        with (
            patch("app.services.import_service.ParserRegistry") as MockRegistry,
            patch("app.services.import_service.CategorizationEngine") as MockEngine,
            patch("app.services.import_service._uploaded_file_path") as mock_fpath,
            patch("app.services.import_service._preview_path") as mock_ppath,
        ):
            mock_reg_inst = MockRegistry.return_value
            mock_reg_inst.parse.return_value = parse_result

            cat_tx = _make_categorized_transactions()[:1]
            mock_eng_inst = MockEngine.return_value
            mock_eng_inst.categorize_batch.return_value = cat_tx

            mock_fpath.return_value = MagicMock()
            mock_ppath.return_value = MagicMock()

            from app.services.import_service import upload_and_parse

            record, categorized = await upload_and_parse(
                db=mock_db,
                user_id=MOCK_USER_ID,
                account_id=MOCK_ACCOUNT_ID,
                filename="test.csv",
                content=b"some,csv,data",
            )

            mock_reg_inst.parse.assert_called_once()
            mock_eng_inst.categorize_batch.assert_called_once()
            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()
            assert len(categorized) == 1

    @pytest.mark.asyncio
    async def test_upload_invalid_extension(self) -> None:
        """upload_and_parse raises 400 for unsupported file extensions."""
        from fastapi import HTTPException

        from app.services.import_service import upload_and_parse

        mock_db = AsyncMock(spec=AsyncSession)

        with pytest.raises(HTTPException) as exc_info:
            await upload_and_parse(
                db=mock_db,
                user_id=MOCK_USER_ID,
                account_id=MOCK_ACCOUNT_ID,
                filename="test.doc",
                content=b"data",
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_parser_not_found(self) -> None:
        """upload_and_parse raises 400 when no parser matches."""
        from fastapi import HTTPException

        from app.services.import_service import upload_and_parse

        mock_db = AsyncMock(spec=AsyncSession)

        with patch("app.services.import_service.ParserRegistry") as MockRegistry:
            mock_reg_inst = MockRegistry.return_value
            mock_reg_inst.parse.side_effect = ValueError("No parser found")

            with pytest.raises(HTTPException) as exc_info:
                await upload_and_parse(
                    db=mock_db,
                    user_id=MOCK_USER_ID,
                    account_id=MOCK_ACCOUNT_ID,
                    filename="test.csv",
                    content=b"bad data",
                )
            assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_get_preview_not_found(self) -> None:
        """get_preview raises 404 when import record doesn't exist."""
        from fastapi import HTTPException

        from app.services.import_service import get_preview

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_preview(db=mock_db, user_id=MOCK_USER_ID, import_id=MOCK_IMPORT_ID)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_preview_wrong_status(self) -> None:
        """get_preview raises 409 when import is already confirmed."""
        from fastapi import HTTPException

        from app.services.import_service import get_preview

        record = _make_import_record(status=ImportStatus.confirmed)
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await get_preview(db=mock_db, user_id=MOCK_USER_ID, import_id=MOCK_IMPORT_ID)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_confirm_wrong_status(self) -> None:
        """confirm_import raises 409 when import is not in preview status."""
        from fastapi import HTTPException

        from app.services.import_service import confirm_import

        record = _make_import_record(status=ImportStatus.confirmed)
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await confirm_import(
                db=mock_db,
                user_id=MOCK_USER_ID,
                import_id=MOCK_IMPORT_ID,
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled(self) -> None:
        """cancel_import raises 409 when import is already cancelled."""
        from fastapi import HTTPException

        from app.services.import_service import cancel_import

        record = _make_import_record(status=ImportStatus.cancelled)
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await cancel_import(
                db=mock_db,
                user_id=MOCK_USER_ID,
                import_id=MOCK_IMPORT_ID,
            )
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_cancel_already_confirmed(self) -> None:
        """cancel_import raises 409 when import is already confirmed."""
        from fastapi import HTTPException

        from app.services.import_service import cancel_import

        record = _make_import_record(status=ImportStatus.confirmed)
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = record
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await cancel_import(
                db=mock_db,
                user_id=MOCK_USER_ID,
                import_id=MOCK_IMPORT_ID,
            )
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Serialization / deserialization tests
# ---------------------------------------------------------------------------


class TestPreviewSerialization:
    """Test preview data JSON round-trip."""

    def test_serialize_roundtrip(self) -> None:
        """Categorized transactions survive JSON serialize → deserialize."""
        from app.services.import_service import (
            _deserialize_categorized,
            _serialize_categorized,
        )

        original = _make_categorized_transactions()
        serialized = _serialize_categorized(original)
        deserialized = _deserialize_categorized(serialized)

        assert len(deserialized) == len(original)
        for orig, deser in zip(original, deserialized, strict=True):
            assert orig.date == deser.date
            assert orig.amount == deser.amount
            assert orig.currency == deser.currency
            assert orig.description == deser.description
            assert orig.type == deser.type
            assert orig.categorization.category_name == deser.categorization.category_name
            assert orig.categorization.confidence == deser.categorization.confidence
            assert orig.categorization.matched_by == deser.categorization.matched_by

    def test_serialize_to_json_valid(self) -> None:
        """Serialized data can be converted to JSON string."""
        from app.services.import_service import _serialize_categorized

        original = _make_categorized_transactions()
        serialized = _serialize_categorized(original)
        json_str = json.dumps(serialized, ensure_ascii=False)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert len(parsed) == 3

    def test_deserialize_preserves_decimal(self) -> None:
        """Deserialized amounts are Decimal instances."""
        from app.services.import_service import (
            _deserialize_categorized,
            _serialize_categorized,
        )

        original = _make_categorized_transactions()
        serialized = _serialize_categorized(original)
        deserialized = _deserialize_categorized(serialized)
        for tx in deserialized:
            assert isinstance(tx.amount, Decimal)


# ---------------------------------------------------------------------------
# File type detection tests
# ---------------------------------------------------------------------------


class TestFileTypeDetection:
    """Test _detect_file_type helper."""

    def test_csv_extension(self) -> None:
        from app.services.import_service import _detect_file_type

        assert _detect_file_type("data.csv") == FileType.csv

    def test_pdf_extension(self) -> None:
        from app.services.import_service import _detect_file_type

        assert _detect_file_type("statement.pdf") == FileType.pdf

    def test_xlsx_extension(self) -> None:
        from app.services.import_service import _detect_file_type

        assert _detect_file_type("report.xlsx") == FileType.xlsx

    def test_unsupported_extension(self) -> None:
        from fastapi import HTTPException

        from app.services.import_service import _detect_file_type

        with pytest.raises(HTTPException) as exc_info:
            _detect_file_type("report.doc")
        assert exc_info.value.status_code == 400

    def test_uppercase_extension(self) -> None:
        from app.services.import_service import _detect_file_type

        assert _detect_file_type("DATA.CSV") == FileType.csv


# ---------------------------------------------------------------------------
# API endpoint tests (with mocked service layer)
# ---------------------------------------------------------------------------


class TestUploadEndpoint:
    """Tests for POST /api/v1/imports/upload."""

    @pytest.mark.asyncio
    async def test_upload_success(self, client: AsyncClient) -> None:
        """Successful CSV upload returns 201 with import record."""
        record = _make_import_record()
        categorized = _make_categorized_transactions()

        with patch(
            "app.api.imports.import_service.upload_and_parse",
            new_callable=AsyncMock,
            return_value=(record, categorized),
        ):
            resp = await client.post(
                "/api/v1/imports/upload",
                files={"file": ("bank_sample.csv", BANK_CSV_CONTENT, "text/csv")},
                data={"account_id": str(MOCK_ACCOUNT_ID)},
            )
        assert resp.status_code == 201
        body = resp.json()
        assert body["filename"] == "bank_sample.csv"
        assert body["status"] == "preview"
        assert body["file_type"] == "csv"

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, client: AsyncClient) -> None:
        """Upload exceeding max size returns 413."""
        big_content = b"x" * (11 * 1024 * 1024)  # 11MB
        resp = await client.post(
            "/api/v1/imports/upload",
            files={"file": ("big.csv", big_content, "text/csv")},
            data={"account_id": str(MOCK_ACCOUNT_ID)},
        )
        assert resp.status_code == 413

    @pytest.mark.asyncio
    async def test_upload_with_source_type(self, client: AsyncClient) -> None:
        """Upload with explicit source_type hint passes it through."""
        record = _make_import_record()
        categorized = _make_categorized_transactions()

        with patch(
            "app.api.imports.import_service.upload_and_parse",
            new_callable=AsyncMock,
            return_value=(record, categorized),
        ) as mock_upload:
            resp = await client.post(
                "/api/v1/imports/upload",
                files={"file": ("bank_sample.csv", BANK_CSV_CONTENT, "text/csv")},
                data={
                    "account_id": str(MOCK_ACCOUNT_ID),
                    "source_type": "satispay",
                },
            )
        assert resp.status_code == 201
        call_kwargs = mock_upload.call_args.kwargs
        assert call_kwargs["source_type_hint"] == "satispay"

    @pytest.mark.asyncio
    async def test_upload_missing_file(self, client: AsyncClient) -> None:
        """Upload without file field returns 422."""
        resp = await client.post(
            "/api/v1/imports/upload",
            data={"account_id": str(MOCK_ACCOUNT_ID)},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_missing_account_id(self, client: AsyncClient) -> None:
        """Upload without account_id returns 422."""
        resp = await client.post(
            "/api/v1/imports/upload",
            files={"file": ("test.csv", b"data", "text/csv")},
        )
        assert resp.status_code == 422


class TestPreviewEndpoint:
    """Tests for GET /api/v1/imports/{import_id}/preview."""

    @pytest.mark.asyncio
    async def test_preview_success(self, client: AsyncClient) -> None:
        """Successful preview returns transactions with categories."""
        record = _make_import_record()
        categorized = _make_categorized_transactions()

        with patch(
            "app.api.imports.import_service.get_preview",
            new_callable=AsyncMock,
            return_value=(record, categorized),
        ):
            resp = await client.get(
                f"/api/v1/imports/{MOCK_IMPORT_ID}/preview",
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["import_id"] == str(MOCK_IMPORT_ID)
        assert body["status"] == "preview"
        assert len(body["transactions"]) == 3
        assert body["transactions"][0]["category_name"] == "Supermercato"
        assert body["transactions"][0]["temp_id"] == 0

    @pytest.mark.asyncio
    async def test_preview_not_found(self, client: AsyncClient) -> None:
        """Preview for non-existent import returns 404."""
        from fastapi import HTTPException

        with patch(
            "app.api.imports.import_service.get_preview",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=404, detail="Import not found."),
        ):
            resp = await client.get(
                f"/api/v1/imports/{uuid.uuid4()}/preview",
            )
        assert resp.status_code == 404


class TestConfirmEndpoint:
    """Tests for POST /api/v1/imports/{import_id}/confirm."""

    @pytest.mark.asyncio
    async def test_confirm_success(self, client: AsyncClient) -> None:
        """Successful confirm returns confirmed status and counts."""
        record = _make_import_record(status=ImportStatus.confirmed, imported_count=3)

        with patch(
            "app.api.imports.import_service.confirm_import",
            new_callable=AsyncMock,
            return_value=(record, 2),
        ):
            resp = await client.post(
                f"/api/v1/imports/{MOCK_IMPORT_ID}/confirm",
                json={},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "confirmed"
        assert body["imported_count"] == 3
        assert body["categorized_count"] == 2

    @pytest.mark.asyncio
    async def test_confirm_with_overrides(self, client: AsyncClient) -> None:
        """Confirm with category_overrides passes them to the service."""
        record = _make_import_record(status=ImportStatus.confirmed, imported_count=3)

        with patch(
            "app.api.imports.import_service.confirm_import",
            new_callable=AsyncMock,
            return_value=(record, 3),
        ) as mock_confirm:
            resp = await client.post(
                f"/api/v1/imports/{MOCK_IMPORT_ID}/confirm",
                json={"category_overrides": {"0": "Alimentari", "2": "Bollette"}},
            )
        assert resp.status_code == 200
        call_kwargs = mock_confirm.call_args.kwargs
        assert call_kwargs["category_overrides"] == {0: "Alimentari", 2: "Bollette"}

    @pytest.mark.asyncio
    async def test_confirm_conflict(self, client: AsyncClient) -> None:
        """Confirm for already confirmed import returns 409."""
        from fastapi import HTTPException

        with patch(
            "app.api.imports.import_service.confirm_import",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=409, detail="Already confirmed"),
        ):
            resp = await client.post(
                f"/api/v1/imports/{MOCK_IMPORT_ID}/confirm",
                json={},
            )
        assert resp.status_code == 409


class TestCancelEndpoint:
    """Tests for DELETE /api/v1/imports/{import_id}."""

    @pytest.mark.asyncio
    async def test_cancel_success(self, client: AsyncClient) -> None:
        """Successful cancel returns 204."""
        with patch(
            "app.api.imports.import_service.cancel_import",
            new_callable=AsyncMock,
            return_value=None,
        ):
            resp = await client.delete(
                f"/api/v1/imports/{MOCK_IMPORT_ID}",
            )
        assert resp.status_code == 204

    @pytest.mark.asyncio
    async def test_cancel_not_found(self, client: AsyncClient) -> None:
        """Cancel for non-existent import returns 404."""
        from fastapi import HTTPException

        with patch(
            "app.api.imports.import_service.cancel_import",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=404, detail="Import not found."),
        ):
            resp = await client.delete(
                f"/api/v1/imports/{uuid.uuid4()}",
            )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cancel_conflict(self, client: AsyncClient) -> None:
        """Cancel for already confirmed import returns 409."""
        from fastapi import HTTPException

        with patch(
            "app.api.imports.import_service.cancel_import",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=409, detail="Already confirmed"),
        ):
            resp = await client.delete(
                f"/api/v1/imports/{MOCK_IMPORT_ID}",
            )
        assert resp.status_code == 409


class TestListEndpoint:
    """Tests for GET /api/v1/imports/."""

    @pytest.mark.asyncio
    async def test_list_imports(self, client: AsyncClient) -> None:
        """List imports returns items and total."""
        records = [
            _make_import_record(),
            _make_import_record(
                import_id=uuid.UUID("00000000-0000-4000-8000-bbb000000002"),
                status=ImportStatus.confirmed,
                imported_count=6,
            ),
        ]

        with patch(
            "app.api.imports.import_service.list_imports",
            new_callable=AsyncMock,
            return_value=records,
        ):
            resp = await client.get("/api/v1/imports/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        assert len(body["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_imports_empty(self, client: AsyncClient) -> None:
        """List imports returns empty list when no imports exist."""
        with patch(
            "app.api.imports.import_service.list_imports",
            new_callable=AsyncMock,
            return_value=[],
        ):
            resp = await client.get("/api/v1/imports/")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 0
        assert body["items"] == []


class TestUnauthorizedAccess:
    """Tests for requests without authentication."""

    @pytest.mark.asyncio
    async def test_upload_no_auth(self) -> None:
        """Upload without auth returns 401/403."""
        # Remove override temporarily
        original_override = app.dependency_overrides.get(get_current_user)
        from fastapi import HTTPException

        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            HTTPException(status_code=401, detail="Not authenticated")
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/v1/imports/upload",
                files={"file": ("test.csv", b"data", "text/csv")},
                data={"account_id": str(MOCK_ACCOUNT_ID)},
            )
        assert resp.status_code == 401

        # Restore override
        if original_override is not None:
            app.dependency_overrides[get_current_user] = original_override
        else:
            app.dependency_overrides[get_current_user] = lambda: _make_mock_user()

    @pytest.mark.asyncio
    async def test_preview_no_auth(self) -> None:
        """Preview without auth returns 401."""
        original_override = app.dependency_overrides.get(get_current_user)
        from fastapi import HTTPException

        app.dependency_overrides[get_current_user] = lambda: (_ for _ in ()).throw(
            HTTPException(status_code=401, detail="Not authenticated")
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(f"/api/v1/imports/{MOCK_IMPORT_ID}/preview")
        assert resp.status_code == 401

        if original_override is not None:
            app.dependency_overrides[get_current_user] = original_override
        else:
            app.dependency_overrides[get_current_user] = lambda: _make_mock_user()


# ---------------------------------------------------------------------------
# Integration-style tests (parser + categorization, no real DB)
# ---------------------------------------------------------------------------


class TestParserCategorizationIntegration:
    """Test that ParserRegistry + CategorizationEngine work together."""

    def test_parse_bank_csv(self) -> None:
        """ParserRegistry parses the bank CSV fixture correctly."""
        from app.services.parser.registry import ParserRegistry

        registry = ParserRegistry()
        result = registry.parse("bank_sample.csv", BANK_CSV_CONTENT)
        assert result.source_type == "bank_csv"
        assert result.parsed_count == 6
        assert len(result.transactions) == 6

    def test_categorize_parsed_transactions(self) -> None:
        """CategorizationEngine categorizes parsed bank CSV transactions."""
        from app.services.categorization.engine import CategorizationEngine
        from app.services.parser.registry import ParserRegistry

        registry = ParserRegistry()
        result = registry.parse("bank_sample.csv", BANK_CSV_CONTENT)

        engine = CategorizationEngine()
        categorized = engine.categorize_batch(result.transactions)

        assert len(categorized) == 6
        for ct in categorized:
            assert ct.categorization is not None
            assert ct.categorization.category_name is not None
            assert ct.categorization.confidence >= 0.0

    def test_full_pipeline_bank_csv(self) -> None:
        """Full parse → categorize pipeline produces valid TransactionPreview data."""
        from app.services.categorization.engine import CategorizationEngine
        from app.services.parser.registry import ParserRegistry

        registry = ParserRegistry()
        result = registry.parse("bank_sample.csv", BANK_CSV_CONTENT)

        engine = CategorizationEngine()
        categorized = engine.categorize_batch(result.transactions)

        previews = [
            TransactionPreview(
                temp_id=idx,
                date=ct.date,
                amount=float(ct.amount),
                currency=ct.currency,
                description=ct.description,
                original_description=ct.original_description,
                type=ct.type,
                category_name=ct.categorization.category_name,
                confidence=ct.categorization.confidence,
                matched_by=ct.categorization.matched_by,
            )
            for idx, ct in enumerate(categorized)
        ]

        assert len(previews) == 6
        assert previews[0].temp_id == 0
        assert previews[-1].temp_id == 5
