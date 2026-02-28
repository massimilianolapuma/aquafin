"""PDF parser for structured bank statement tables."""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .base import BaseParser, ParseResult, RawTransaction

# Column name variants (lowercase) — shared with bank_csv
_DATE_COLUMNS = {
    "data",
    "data operazione",
    "data contabile",
    "data valuta",
    "data movimento",
}
_DESCRIPTION_COLUMNS = {
    "descrizione",
    "causale",
    "descrizione operazione",
    "dettagli",
    "movimento",
}
_SINGLE_AMOUNT_COLUMNS = {
    "importo",
    "importo eur",
    "importo (eur)",
    "ammontare",
}
_DEBIT_COLUMNS = {"dare", "addebiti", "uscite", "addebito"}
_CREDIT_COLUMNS = {"avere", "accrediti", "entrate", "accredito"}


def _parse_italian_date(value: str) -> date:
    """Parse Italian date formats: dd/mm/yyyy, dd-mm-yyyy, dd.mm.yyyy."""
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {value!r}")


def _parse_italian_amount(value: str) -> Decimal:
    """Parse Italian number format: 1.234,56 → Decimal('1234.56').

    Also handles plain formats like -45.80 when no comma is present.
    """
    value = value.strip()
    if not value:
        raise ValueError("Empty amount")

    # Remove currency symbols / whitespace
    value = re.sub(r"[€$£\s]", "", value)

    if "," in value:
        # Italian format: dots are thousands separators, comma is decimal
        value = value.replace(".", "").replace(",", ".")
    # else: assume standard decimal notation (e.g. -45.80)

    return Decimal(value)


def _find_column_index(headers: list[str], candidates: set[str]) -> int | None:
    """Return the index of the first header matching a candidate, or None."""
    for i, h in enumerate(headers):
        if h.strip().lower() in candidates:
            return i
    return None


class PDFParser(BaseParser):
    """Parser for PDF bank statements containing structured tables."""

    SOURCE_TYPE = "pdf"

    # ------------------------------------------------------------------ #
    # Detection
    # ------------------------------------------------------------------ #

    def detect(self, file_path: str, content: bytes) -> bool:
        """Detect PDF by checking for the %PDF magic bytes."""
        return content[:5] == b"%PDF-"

    # ------------------------------------------------------------------ #
    # Column mapping
    # ------------------------------------------------------------------ #

    def get_column_mapping(self) -> dict[str, str]:
        """Return generic column mapping for PDF table columns."""
        return {
            "Data": "date",
            "Descrizione": "description",
            "Importo": "amount",
            "Dare": "debit",
            "Avere": "credit",
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def _detect_header_row(table: list[list[str | None]]) -> int | None:
        """Find the row index that looks like a header (contains known column names)."""
        for i, row in enumerate(table):
            if row is None:
                continue
            lowered = {(cell or "").strip().lower() for cell in row}
            has_date = bool(lowered & _DATE_COLUMNS)
            has_desc = bool(lowered & _DESCRIPTION_COLUMNS)
            has_amount = bool(lowered & _SINGLE_AMOUNT_COLUMNS) or (
                bool(lowered & _DEBIT_COLUMNS) or bool(lowered & _CREDIT_COLUMNS)
            )
            if has_date and (has_desc or has_amount):
                return i
        return None

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Parse a PDF bank statement and return normalized transactions."""
        try:
            import pdfplumber
        except ImportError as exc:
            raise ImportError(
                "pdfplumber is required for PDF parsing. "
                "Install it with: pip install 'aquafin-backend[parser]'"
            ) from exc

        if not content or not content.strip():
            return ParseResult(
                transactions=[],
                source_type=self.SOURCE_TYPE,
                row_count=0,
                parsed_count=0,
            )

        transactions: list[RawTransaction] = []
        errors: list[str] = []
        total_rows = 0

        try:
            pdf = pdfplumber.open(io.BytesIO(content))
        except Exception as exc:
            return ParseResult(
                transactions=[],
                source_type=self.SOURCE_TYPE,
                row_count=0,
                parsed_count=0,
                errors=[f"Failed to open PDF: {exc}"],
            )

        try:
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                if not tables:
                    errors.append(f"Page {page_num}: no tables found")
                    continue

                for table in tables:
                    if not table or len(table) < 2:
                        errors.append(f"Page {page_num}: table too small (< 2 rows)")
                        continue

                    header_idx = self._detect_header_row(table)
                    if header_idx is None:
                        errors.append(f"Page {page_num}: no recognizable header row")
                        continue

                    headers = [(cell or "").strip() for cell in table[header_idx]]
                    data_rows = table[header_idx + 1 :]

                    # Resolve column indices
                    date_idx = _find_column_index(headers, _DATE_COLUMNS)
                    desc_idx = _find_column_index(headers, _DESCRIPTION_COLUMNS)
                    amount_idx = _find_column_index(headers, _SINGLE_AMOUNT_COLUMNS)
                    debit_idx = _find_column_index(headers, _DEBIT_COLUMNS)
                    credit_idx = _find_column_index(headers, _CREDIT_COLUMNS)

                    if date_idx is None:
                        errors.append(f"Page {page_num}: no date column found")
                        continue

                    for row_offset, row in enumerate(data_rows):
                        total_rows += 1
                        row_label = f"Page {page_num}, row {row_offset + 1}"

                        if row is None:
                            errors.append(f"{row_label}: empty row")
                            continue

                        try:
                            # Get cell values safely
                            date_val = (row[date_idx] or "").strip() if date_idx < len(row) else ""
                            if not date_val:
                                errors.append(f"{row_label}: empty date")
                                continue

                            parsed_date = _parse_italian_date(date_val)

                            # Description
                            desc_val = ""
                            if desc_idx is not None and desc_idx < len(row):
                                desc_val = (row[desc_idx] or "").strip()
                            original_desc = desc_val
                            description = " ".join(desc_val.split())  # normalize whitespace

                            # Amount
                            amount: Decimal | None = None
                            if amount_idx is not None and amount_idx < len(row):
                                amt_str = (row[amount_idx] or "").strip()
                                if amt_str:
                                    amount = _parse_italian_amount(amt_str)

                            if amount is None and (debit_idx is not None or credit_idx is not None):
                                debit = Decimal("0")
                                credit = Decimal("0")
                                if debit_idx is not None and debit_idx < len(row):
                                    d_str = (row[debit_idx] or "").strip()
                                    if d_str:
                                        debit = _parse_italian_amount(d_str)
                                if credit_idx is not None and credit_idx < len(row):
                                    c_str = (row[credit_idx] or "").strip()
                                    if c_str:
                                        credit = _parse_italian_amount(c_str)
                                amount = credit - abs(debit)

                            if amount is None:
                                errors.append(f"{row_label}: no amount found")
                                continue

                            tx_type = "income" if amount >= 0 else "expense"

                            transactions.append(
                                RawTransaction(
                                    date=parsed_date,
                                    amount=amount,
                                    currency="EUR",
                                    description=description,
                                    original_description=original_desc,
                                    type=tx_type,
                                    metadata={"source_page": page_num},
                                )
                            )
                        except (ValueError, InvalidOperation, IndexError) as exc:
                            errors.append(f"{row_label}: {exc}")
        finally:
            pdf.close()

        return ParseResult(
            transactions=transactions,
            source_type=self.SOURCE_TYPE,
            row_count=total_rows,
            parsed_count=len(transactions),
            errors=errors,
        )
