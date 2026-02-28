"""Tests for BankCSVParser."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.parser.bank_csv import BankCSVParser

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def parser() -> BankCSVParser:
    return BankCSVParser()


@pytest.fixture
def bank_content() -> bytes:
    return (FIXTURES / "bank_sample.csv").read_bytes()


@pytest.fixture
def satispay_content() -> bytes:
    return (FIXTURES / "satispay_sample.csv").read_bytes()


@pytest.fixture
def paypal_content() -> bytes:
    return (FIXTURES / "paypal_sample.csv").read_bytes()


# ------------------------------------------------------------------ #
# detect()
# ------------------------------------------------------------------ #


class TestDetect:
    def test_detect_bank_csv(self, parser: BankCSVParser, bank_content: bytes) -> None:
        assert parser.detect("bank.csv", bank_content) is True

    def test_reject_satispay(self, parser: BankCSVParser, satispay_content: bytes) -> None:
        assert parser.detect("satispay.csv", satispay_content) is False

    def test_reject_paypal(self, parser: BankCSVParser, paypal_content: bytes) -> None:
        assert parser.detect("paypal.csv", paypal_content) is False

    def test_reject_empty(self, parser: BankCSVParser) -> None:
        assert parser.detect("empty.csv", b"") is False
        assert parser.detect("empty.csv", b"   ") is False


# ------------------------------------------------------------------ #
# parse() — basic
# ------------------------------------------------------------------ #


class TestParse:
    def test_transaction_count(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        assert result.source_type == "bank_csv"
        assert result.row_count == 6
        assert result.parsed_count == 6
        assert len(result.transactions) == 6
        assert result.errors == []

    def test_empty_file(self, parser: BankCSVParser) -> None:
        result = parser.parse("empty.csv", b"")
        assert result.parsed_count == 0
        assert result.transactions == []

    def test_header_only(self, parser: BankCSVParser) -> None:
        content = b"Data Operazione;Data Valuta;Descrizione;Importo\n"
        result = parser.parse("header.csv", content)
        assert result.parsed_count == 0
        assert result.transactions == []


# ------------------------------------------------------------------ #
# Italian date parsing
# ------------------------------------------------------------------ #


class TestDateParsing:
    def test_slash_format(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        assert result.transactions[0].date == date(2025, 3, 1)
        assert result.transactions[2].date == date(2025, 3, 5)

    def test_dash_format(self, parser: BankCSVParser) -> None:
        content = b"Data Operazione;Descrizione;Importo\n01-03-2025;Test;-10,00\n"
        result = parser.parse("test.csv", content)
        assert result.transactions[0].date == date(2025, 3, 1)

    def test_dot_format(self, parser: BankCSVParser) -> None:
        content = b"Data Operazione;Descrizione;Importo\n01.03.2025;Test;-10,00\n"
        result = parser.parse("test.csv", content)
        assert result.transactions[0].date == date(2025, 3, 1)


# ------------------------------------------------------------------ #
# Italian number parsing
# ------------------------------------------------------------------ #


class TestAmountParsing:
    def test_simple_negative(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        assert result.transactions[0].amount == Decimal("-45.80")

    def test_thousands_separator(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        # 2.350,00 → 2350.00
        assert result.transactions[1].amount == Decimal("2350.00")

    def test_positive_amount(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        assert result.transactions[5].amount == Decimal("500.00")


# ------------------------------------------------------------------ #
# Type inference
# ------------------------------------------------------------------ #


class TestTypeInference:
    def test_expense(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        assert result.transactions[0].type == "expense"
        assert result.transactions[2].type == "expense"

    def test_income(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        assert result.transactions[1].type == "income"
        assert result.transactions[5].type == "income"


# ------------------------------------------------------------------ #
# Description normalization
# ------------------------------------------------------------------ #


class TestDescription:
    def test_description_preserved(self, parser: BankCSVParser, bank_content: bytes) -> None:
        result = parser.parse("bank.csv", bank_content)
        assert "ESSELUNGA" in result.transactions[0].description
        assert result.transactions[0].original_description == "PAGAMENTO POS ESSELUNGA VIA ROMA MI"


# ------------------------------------------------------------------ #
# Encoding fallback
# ------------------------------------------------------------------ #


class TestEncoding:
    def test_latin1_fallback(self, parser: BankCSVParser) -> None:
        # Create content with Latin-1 characters that are not valid UTF-8
        header = "Data Operazione;Descrizione;Importo\n"
        row = "01/03/2025;PAGAMENTO CAFFÈ;-2,50\n"
        content = (header + row).encode("latin-1")
        result = parser.parse("latin1.csv", content)
        assert result.parsed_count == 1
        assert "CAFFÈ" in result.transactions[0].description

    def test_utf8_bom(self, parser: BankCSVParser) -> None:
        content = "\ufeffData Operazione;Descrizione;Importo\n01/03/2025;Test;-10,00\n"
        result = parser.parse("bom.csv", content.encode("utf-8-sig"))
        assert result.parsed_count == 1


# ------------------------------------------------------------------ #
# Malformed rows
# ------------------------------------------------------------------ #


class TestMalformedRows:
    def test_bad_date_skipped(self, parser: BankCSVParser) -> None:
        content = (
            b"Data Operazione;Descrizione;Importo\n"
            b"INVALID;Test;-10,00\n"
            b"01/03/2025;Good Row;-5,00\n"
        )
        result = parser.parse("bad.csv", content)
        assert result.parsed_count == 1
        assert len(result.errors) == 1

    def test_bad_amount_skipped(self, parser: BankCSVParser) -> None:
        content = (
            b"Data Operazione;Descrizione;Importo\n"
            b"01/03/2025;Test;NOT_A_NUMBER\n"
            b"01/03/2025;Good Row;-5,00\n"
        )
        result = parser.parse("bad.csv", content)
        assert result.parsed_count == 1
        assert len(result.errors) == 1


# ------------------------------------------------------------------ #
# Dare/Avere columns
# ------------------------------------------------------------------ #


class TestDareAvere:
    def test_separate_debit_credit_columns(self, parser: BankCSVParser) -> None:
        content = (
            b"Data;Descrizione;Dare;Avere\n"
            b"01/03/2025;Spesa;50,00;\n"
            b"02/03/2025;Stipendio;;1.500,00\n"
        )
        result = parser.parse("dare_avere.csv", content)
        assert result.parsed_count == 2
        # Dare (debit) → negative
        assert result.transactions[0].amount == Decimal("-50.00")
        assert result.transactions[0].type == "expense"
        # Avere (credit) → positive
        assert result.transactions[1].amount == Decimal("1500.00")
        assert result.transactions[1].type == "income"
