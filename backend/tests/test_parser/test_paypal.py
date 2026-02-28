"""Tests for PayPalParser."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.parser.paypal import PayPalParser

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def parser() -> PayPalParser:
    return PayPalParser()


@pytest.fixture
def paypal_content() -> bytes:
    return (FIXTURES / "paypal_sample.csv").read_bytes()


@pytest.fixture
def bank_content() -> bytes:
    return (FIXTURES / "bank_sample.csv").read_bytes()


@pytest.fixture
def satispay_content() -> bytes:
    return (FIXTURES / "satispay_sample.csv").read_bytes()


# ------------------------------------------------------------------ #
# detect()
# ------------------------------------------------------------------ #


class TestDetect:
    def test_detect_paypal(self, parser: PayPalParser, paypal_content: bytes) -> None:
        assert parser.detect("paypal.csv", paypal_content) is True

    def test_reject_bank_csv(self, parser: PayPalParser, bank_content: bytes) -> None:
        assert parser.detect("bank.csv", bank_content) is False

    def test_reject_satispay(self, parser: PayPalParser, satispay_content: bytes) -> None:
        assert parser.detect("satispay.csv", satispay_content) is False

    def test_reject_empty(self, parser: PayPalParser) -> None:
        assert parser.detect("empty.csv", b"") is False


# ------------------------------------------------------------------ #
# parse() — uses Gross amount
# ------------------------------------------------------------------ #


class TestParse:
    def test_transaction_count(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert result.source_type == "paypal"
        assert result.row_count == 5
        assert result.parsed_count == 5
        assert len(result.transactions) == 5
        assert result.errors == []

    def test_uses_gross_not_net(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        # Netflix: Gross=-15.99, Net=-16.49 → should use Gross
        assert result.transactions[0].amount == Decimal("-15.99")

    def test_date_parsing(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        # mm/dd/yyyy format: 03/01/2025 → March 1, 2025
        assert result.transactions[0].date == date(2025, 3, 1)
        assert result.transactions[4].date == date(2025, 3, 20)

    def test_currency(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert all(tx.currency == "EUR" for tx in result.transactions)

    def test_empty_file(self, parser: PayPalParser) -> None:
        result = parser.parse("empty.csv", b"")
        assert result.parsed_count == 0
        assert result.transactions == []


# ------------------------------------------------------------------ #
# Fee stored in metadata
# ------------------------------------------------------------------ #


class TestMetadata:
    def test_fee_in_metadata(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        # Netflix fee: -0.50
        assert result.transactions[0].metadata["fee"] == str(Decimal("-0.50"))

    def test_net_in_metadata(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert result.transactions[0].metadata["net"] == str(Decimal("-16.49"))

    def test_status_in_metadata(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert result.transactions[0].metadata["status"] == "Completed"

    def test_paypal_type_in_metadata(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert result.transactions[0].metadata["paypal_type"] == "Payment"


# ------------------------------------------------------------------ #
# Type mapping
# ------------------------------------------------------------------ #


class TestTypeMapping:
    def test_payment_is_expense(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert result.transactions[0].type == "expense"  # Payment

    def test_refund_is_income(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert result.transactions[1].type == "income"  # Refund

    def test_transfer(self, parser: PayPalParser, paypal_content: bytes) -> None:
        result = parser.parse("paypal.csv", paypal_content)
        assert result.transactions[4].type == "transfer"  # Transfer


# ------------------------------------------------------------------ #
# Italian columns
# ------------------------------------------------------------------ #


class TestItalianColumns:
    def test_italian_headers(self, parser: PayPalParser) -> None:
        content = (
            b"Data,Nome,Tipo,Stato,Valuta,Lordo,Tariffa,Netto\n"
            b"03/01/2025,Netflix,Pagamento,Completato,EUR,-15.99,-0.50,-16.49\n"
        )
        assert parser.detect("it.csv", content) is True
        result = parser.parse("it.csv", content)
        assert result.parsed_count == 1
        assert result.transactions[0].amount == Decimal("-15.99")


# ------------------------------------------------------------------ #
# Malformed rows
# ------------------------------------------------------------------ #


class TestMalformedRows:
    def test_bad_date_skipped(self, parser: PayPalParser) -> None:
        content = (
            b"Date,Name,Type,Status,Currency,Gross,Fee,Net\n"
            b"BADDATE,Test,Payment,Completed,EUR,-10.00,0.00,-10.00\n"
            b"03/01/2025,Good,Payment,Completed,EUR,-5.00,0.00,-5.00\n"
        )
        result = parser.parse("bad.csv", content)
        assert result.parsed_count == 1
        assert len(result.errors) == 1
