"""Tests for SatispayParser."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.parser.satispay import SatispayParser

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def parser() -> SatispayParser:
    return SatispayParser()


@pytest.fixture
def satispay_content() -> bytes:
    return (FIXTURES / "satispay_sample.csv").read_bytes()


@pytest.fixture
def bank_content() -> bytes:
    return (FIXTURES / "bank_sample.csv").read_bytes()


@pytest.fixture
def paypal_content() -> bytes:
    return (FIXTURES / "paypal_sample.csv").read_bytes()


# ------------------------------------------------------------------ #
# detect()
# ------------------------------------------------------------------ #


class TestDetect:
    def test_detect_satispay(self, parser: SatispayParser, satispay_content: bytes) -> None:
        assert parser.detect("satispay.csv", satispay_content) is True

    def test_reject_bank_csv(self, parser: SatispayParser, bank_content: bytes) -> None:
        assert parser.detect("bank.csv", bank_content) is False

    def test_reject_paypal(self, parser: SatispayParser, paypal_content: bytes) -> None:
        assert parser.detect("paypal.csv", paypal_content) is False

    def test_reject_empty(self, parser: SatispayParser) -> None:
        assert parser.detect("empty.csv", b"") is False


# ------------------------------------------------------------------ #
# parse() — field mapping
# ------------------------------------------------------------------ #


class TestParse:
    def test_transaction_count(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert result.source_type == "satispay"
        assert result.row_count == 5
        assert result.parsed_count == 5
        assert len(result.transactions) == 5
        assert result.errors == []

    def test_date_parsing(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert result.transactions[0].date == date(2025, 3, 1)
        assert result.transactions[2].date == date(2025, 3, 5)

    def test_amount(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert result.transactions[0].amount == Decimal("-12.50")
        assert result.transactions[1].amount == Decimal("0.25")

    def test_currency(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert all(tx.currency == "EUR" for tx in result.transactions)

    def test_description_combined(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        # Name + Description combined
        assert "Bar Roma" in result.transactions[0].description
        assert "Caffè e cornetto" in result.transactions[0].description

    def test_metadata_satispay_id(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert result.transactions[0].metadata["satispay_id"] == "SAT001"

    def test_empty_file(self, parser: SatispayParser) -> None:
        result = parser.parse("empty.csv", b"")
        assert result.parsed_count == 0
        assert result.transactions == []


# ------------------------------------------------------------------ #
# Type mapping
# ------------------------------------------------------------------ #


class TestTypeMapping:
    def test_payment_is_expense(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert result.transactions[0].type == "expense"  # Payment

    def test_cashback_is_income(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert result.transactions[1].type == "income"  # Cashback

    def test_refund_is_income(self, parser: SatispayParser, satispay_content: bytes) -> None:
        result = parser.parse("satispay.csv", satispay_content)
        assert result.transactions[3].type == "income"  # Refund


# ------------------------------------------------------------------ #
# Italian columns
# ------------------------------------------------------------------ #


class TestItalianColumns:
    def test_italian_headers(self, parser: SatispayParser) -> None:
        content = (
            b"ID,Data,Tipo,Importo,Valuta,Nome,Descrizione\n"
            b"IT001,01/03/2025,Pagamento,-5.00,EUR,Bar,Espresso\n"
        )
        assert parser.detect("it.csv", content) is True
        result = parser.parse("it.csv", content)
        assert result.parsed_count == 1
        assert result.transactions[0].type == "expense"


# ------------------------------------------------------------------ #
# Malformed rows
# ------------------------------------------------------------------ #


class TestMalformedRows:
    def test_bad_date_skipped(self, parser: SatispayParser) -> None:
        content = (
            b"ID,Date,Type,Amount,Currency,Name,Description\n"
            b"S1,BADDATE,Payment,-5.00,EUR,Test,Desc\n"
            b"S2,2025-03-01,Payment,-3.00,EUR,Good,OK\n"
        )
        result = parser.parse("bad.csv", content)
        assert result.parsed_count == 1
        assert len(result.errors) == 1
