"""Tests for the PDF parser."""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.parser.pdf_parser import PDFParser, _parse_italian_amount, _parse_italian_date


# ---------------------------------------------------------------------------
# Helper: generate PDF bytes with a table using fpdf2
# ---------------------------------------------------------------------------


def _make_pdf_with_table(rows: list[list[str]], *, pages: int = 1) -> bytes:
    """Create a minimal PDF containing a table with the given rows.

    ``rows[0]`` is treated as the header row.
    If *pages* > 1 the same table is repeated on each page.
    """
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=False)

    for _ in range(pages):
        pdf.add_page()
        pdf.set_font("Helvetica", size=9)
        num_cols = len(rows[0])
        col_width = (pdf.w - 2 * pdf.l_margin) / num_cols
        row_height = 8

        for row in rows:
            for cell in row:
                pdf.cell(col_width, row_height, cell, border=1)
            pdf.ln(row_height)

    return bytes(pdf.output())


def _make_empty_pdf() -> bytes:
    """Create a valid PDF with no content (no tables)."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, "No tables here", ln=True)
    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

HEADER = ["Data", "Descrizione", "Importo"]

SAMPLE_ROWS = [
    HEADER,
    ["15/01/2025", "Pagamento bolletta", "-120,50"],
    ["20/01/2025", "Stipendio gennaio", "2.500,00"],
    ["25/01/2025", "Spesa supermercato", "-45,30"],
]

HEADER_DARE_AVERE = ["Data Operazione", "Causale", "Dare", "Avere"]

SAMPLE_ROWS_DARE_AVERE = [
    HEADER_DARE_AVERE,
    ["01/02/2025", "Prelievo ATM", "100,00", ""],
    ["05/02/2025", "Bonifico in entrata", "", "1.000,00"],
]


# ===========================================================================
# Tests
# ===========================================================================


class TestDetect:
    """Tests for PDFParser.detect()."""

    def test_detect_pdf_content(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(SAMPLE_ROWS)
        assert parser.detect("statement.pdf", pdf_bytes) is True

    def test_detect_pdf_magic_bytes(self) -> None:
        parser = PDFParser()
        assert parser.detect("file.pdf", b"%PDF-1.4 fake") is True

    def test_detect_rejects_csv(self) -> None:
        parser = PDFParser()
        csv_content = b"Data;Descrizione;Importo\n01/01/2025;Test;100,00"
        assert parser.detect("file.csv", csv_content) is False

    def test_detect_rejects_empty(self) -> None:
        parser = PDFParser()
        assert parser.detect("file.pdf", b"") is False


class TestItalianDateParsing:
    """Tests for _parse_italian_date helper."""

    def test_slash_format(self) -> None:
        from datetime import date

        assert _parse_italian_date("15/01/2025") == date(2025, 1, 15)

    def test_dash_format(self) -> None:
        from datetime import date

        assert _parse_italian_date("15-01-2025") == date(2025, 1, 15)

    def test_dot_format(self) -> None:
        from datetime import date

        assert _parse_italian_date("15.01.2025") == date(2025, 1, 15)

    def test_invalid_date(self) -> None:
        with pytest.raises(ValueError, match="Cannot parse date"):
            _parse_italian_date("2025/01/15")


class TestItalianAmountParsing:
    """Tests for _parse_italian_amount helper."""

    def test_comma_decimal(self) -> None:
        assert _parse_italian_amount("120,50") == Decimal("120.50")

    def test_dot_thousands_comma_decimal(self) -> None:
        assert _parse_italian_amount("2.500,00") == Decimal("2500.00")

    def test_negative(self) -> None:
        assert _parse_italian_amount("-45,30") == Decimal("-45.30")

    def test_plain_decimal(self) -> None:
        assert _parse_italian_amount("-45.30") == Decimal("-45.30")

    def test_currency_symbol_stripped(self) -> None:
        assert _parse_italian_amount("€ 100,00") == Decimal("100.00")

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="Empty amount"):
            _parse_italian_amount("")


class TestParseSinglePage:
    """Tests for parsing a single-page PDF with an amount column."""

    def test_parse_basic_table(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(SAMPLE_ROWS)
        result = parser.parse("statement.pdf", pdf_bytes)

        assert result.source_type == "pdf"
        assert result.parsed_count == 3
        assert result.row_count == 3
        assert len(result.transactions) == 3

    def test_transaction_values(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(SAMPLE_ROWS)
        result = parser.parse("statement.pdf", pdf_bytes)

        tx0 = result.transactions[0]
        from datetime import date

        assert tx0.date == date(2025, 1, 15)
        assert tx0.amount == Decimal("-120.50")
        assert tx0.currency == "EUR"
        assert tx0.type == "expense"
        assert "bolletta" in tx0.description.lower()

    def test_income_transaction(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(SAMPLE_ROWS)
        result = parser.parse("statement.pdf", pdf_bytes)

        tx1 = result.transactions[1]
        assert tx1.amount == Decimal("2500.00")
        assert tx1.type == "income"

    def test_description_whitespace_normalized(self) -> None:
        rows = [
            HEADER,
            ["10/03/2025", "  Pagamento   con  spazi  ", "-10,00"],
        ]
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(rows)
        result = parser.parse("statement.pdf", pdf_bytes)

        assert result.transactions[0].description == "Pagamento con spazi"


class TestParseDareAvere:
    """Tests for parsing PDFs with separate Dare/Avere columns."""

    def test_dare_avere_columns(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(SAMPLE_ROWS_DARE_AVERE)
        result = parser.parse("statement.pdf", pdf_bytes)

        assert result.parsed_count == 2
        # First row is a debit (Dare)
        assert result.transactions[0].type == "expense"
        assert result.transactions[0].amount == Decimal("-100.00")
        # Second row is a credit (Avere)
        assert result.transactions[1].type == "income"
        assert result.transactions[1].amount == Decimal("1000.00")


class TestParseMultiPage:
    """Tests for multi-page PDF parsing."""

    def test_multi_page_pdf(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(SAMPLE_ROWS, pages=3)
        result = parser.parse("statement.pdf", pdf_bytes)

        # 3 data rows × 3 pages = 9 transactions
        assert result.parsed_count == 9
        assert result.row_count == 9
        assert len(result.transactions) == 9


class TestParseEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_content(self) -> None:
        parser = PDFParser()
        result = parser.parse("empty.pdf", b"")

        assert result.parsed_count == 0
        assert result.row_count == 0
        assert result.transactions == []

    def test_empty_pdf_no_tables(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_empty_pdf()
        result = parser.parse("no_tables.pdf", pdf_bytes)

        assert result.parsed_count == 0
        assert len(result.errors) > 0
        assert any("no tables found" in e.lower() for e in result.errors)

    def test_malformed_rows_skipped(self) -> None:
        rows = [
            HEADER,
            ["15/01/2025", "Valido", "-50,00"],
            ["not-a-date", "Invalido", "abc"],
            ["20/01/2025", "Altro valido", "100,00"],
        ]
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(rows)
        result = parser.parse("mixed.pdf", pdf_bytes)

        assert result.parsed_count == 2
        assert len(result.errors) > 0

    def test_invalid_pdf_bytes(self) -> None:
        parser = PDFParser()
        result = parser.parse("bad.pdf", b"%PDF-1.4 this is not a real PDF")

        assert result.parsed_count == 0
        assert len(result.errors) > 0

    def test_metadata_contains_source_page(self) -> None:
        parser = PDFParser()
        pdf_bytes = _make_pdf_with_table(SAMPLE_ROWS)
        result = parser.parse("statement.pdf", pdf_bytes)

        for tx in result.transactions:
            assert "source_page" in tx.metadata


class TestGetColumnMapping:
    """Test get_column_mapping returns expected keys."""

    def test_mapping_keys(self) -> None:
        parser = PDFParser()
        mapping = parser.get_column_mapping()
        assert "Data" in mapping
        assert "Descrizione" in mapping
        assert "Importo" in mapping
