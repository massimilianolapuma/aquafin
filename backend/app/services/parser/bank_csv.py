"""Italian bank CSV parser."""
from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from .base import BaseParser, ParseResult, RawTransaction

# Column name variants for Italian bank CSV exports (lowercase for matching)
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
    "movimento",
}
_DEBIT_COLUMNS = {"dare", "addebiti", "uscite", "addebito"}
_CREDIT_COLUMNS = {"avere", "accrediti", "entrate", "accredito"}


def _decode_content(content: bytes) -> str:
    """Decode bytes trying UTF-8 first, then Latin-1 fallback."""
    try:
        return content.decode("utf-8-sig")  # handles BOM as well
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _detect_delimiter(text: str) -> str:
    """Auto-detect CSV delimiter from the first lines of text."""
    first_lines = text.split("\n", 5)[:5]
    sample = "\n".join(first_lines)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        return dialect.delimiter
    except csv.Error:
        # Default to semicolon — most common for Italian bank exports
        return ";"


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


class BankCSVParser(BaseParser):
    """Parser for Italian bank CSV exports."""

    SOURCE_TYPE = "bank_csv"

    # ------------------------------------------------------------------ #
    # Detection
    # ------------------------------------------------------------------ #

    def detect(self, file_path: str, content: bytes) -> bool:
        """Detect Italian bank CSV by checking for known column names."""
        if not content.strip():
            return False

        text = _decode_content(content)
        delimiter = _detect_delimiter(text)

        reader = io.StringIO(text)
        try:
            first_line = reader.readline()
        except Exception:
            return False

        headers = {h.strip().lower() for h in first_line.split(delimiter)}

        has_date = bool(headers & _DATE_COLUMNS)
        has_desc = bool(headers & _DESCRIPTION_COLUMNS)
        has_amount = bool(headers & _SINGLE_AMOUNT_COLUMNS) or (
            bool(headers & _DEBIT_COLUMNS) and bool(headers & _CREDIT_COLUMNS)
        )

        return has_date and has_desc and has_amount

    # ------------------------------------------------------------------ #
    # Column mapping
    # ------------------------------------------------------------------ #

    def get_column_mapping(self) -> dict[str, str]:
        """Return generic column mapping (actual mapping is dynamic)."""
        return {
            "Data Operazione": "date",
            "Descrizione": "description",
            "Importo": "amount",
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _find_column(self, columns: pd.Index, candidates: set[str]) -> str | None:
        """Find the first column whose lowered name matches a candidate."""
        for col in columns:
            if col.strip().lower() in candidates:
                return col
        return None

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Parse an Italian bank CSV and return normalized transactions."""
        if not content.strip():
            return ParseResult(
                transactions=[],
                source_type=self.SOURCE_TYPE,
                row_count=0,
                parsed_count=0,
            )

        text = _decode_content(content)
        delimiter = _detect_delimiter(text)

        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype=str,
            keep_default_na=False,
            skipinitialspace=True,
        )

        # Strip column names
        df.columns = df.columns.str.strip()

        # Resolve columns dynamically
        date_col = self._find_column(df.columns, _DATE_COLUMNS)
        desc_col = self._find_column(df.columns, _DESCRIPTION_COLUMNS)
        amount_col = self._find_column(df.columns, _SINGLE_AMOUNT_COLUMNS)
        debit_col = self._find_column(df.columns, _DEBIT_COLUMNS)
        credit_col = self._find_column(df.columns, _CREDIT_COLUMNS)

        if date_col is None or desc_col is None:
            return ParseResult(
                transactions=[],
                source_type=self.SOURCE_TYPE,
                row_count=len(df),
                parsed_count=0,
                errors=["Missing required date or description column"],
            )

        transactions: list[RawTransaction] = []
        errors: list[str] = []

        for idx, row in df.iterrows():
            row_num = int(idx) + 2  # +2: header is row 1, pandas 0-indexed
            try:
                parsed_date = _parse_italian_date(str(row[date_col]))

                # Determine amount
                if amount_col is not None:
                    amount = _parse_italian_amount(str(row[amount_col]))
                elif debit_col is not None and credit_col is not None:
                    debit_str = str(row[debit_col]).strip()
                    credit_str = str(row[credit_col]).strip()
                    debit = _parse_italian_amount(debit_str) if debit_str else Decimal("0")
                    credit = _parse_italian_amount(credit_str) if credit_str else Decimal("0")
                    # Debit values are expenses (negative), credit values are income
                    amount = credit - abs(debit)
                else:
                    errors.append(f"Row {row_num}: no amount column found")
                    continue

                original_desc = str(row[desc_col])
                description = " ".join(original_desc.split())  # normalize whitespace

                tx_type = "income" if amount >= 0 else "expense"

                # Collect extra columns as metadata
                metadata: dict = {}
                valuta_col = self._find_column(df.columns, {"data valuta"})
                if valuta_col and valuta_col != date_col:
                    metadata["data_valuta"] = str(row[valuta_col]).strip()

                transactions.append(
                    RawTransaction(
                        date=parsed_date,
                        amount=amount,
                        currency="EUR",
                        description=description,
                        original_description=original_desc,
                        type=tx_type,
                        metadata=metadata,
                    )
                )
            except (ValueError, InvalidOperation, KeyError) as exc:
                errors.append(f"Row {row_num}: {exc}")

        return ParseResult(
            transactions=transactions,
            source_type=self.SOURCE_TYPE,
            row_count=len(df),
            parsed_count=len(transactions),
            errors=errors,
        )
