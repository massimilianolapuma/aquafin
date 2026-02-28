"""Satispay CSV export parser."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from .base import BaseParser, ParseResult, RawTransaction

# English and Italian column name variants (lowercase for matching)
_REQUIRED_EN = {"id", "date", "type", "amount", "currency", "name"}
_REQUIRED_IT = {"id", "data", "tipo", "importo", "valuta", "nome"}

# Column aliases → canonical keys
_COLUMN_ALIASES: dict[str, str] = {
    # English
    "id": "id",
    "date": "date",
    "type": "type",
    "amount": "amount",
    "currency": "currency",
    "name": "name",
    "description": "description",
    # Italian
    "data": "date",
    "tipo": "type",
    "importo": "amount",
    "valuta": "currency",
    "nome": "name",
    "descrizione": "description",
}

# Satispay type → transaction type
_TYPE_MAP: dict[str, str] = {
    "payment": "expense",
    "refund": "income",
    "top up": "income",
    "cashback": "income",
    # Italian variants
    "pagamento": "expense",
    "rimborso": "income",
    "ricarica": "income",
}


def _decode_content(content: bytes) -> str:
    """Decode bytes trying UTF-8 first, then Latin-1 fallback."""
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("latin-1")


def _detect_delimiter(text: str) -> str:
    """Auto-detect CSV delimiter."""
    first_lines = text.split("\n", 5)[:5]
    sample = "\n".join(first_lines)
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        return ","


def _parse_date(value: str) -> date:
    """Parse date in ISO or Italian formats."""
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {value!r}")


def _parse_amount(value: str) -> Decimal:
    """Parse amount handling both dot-decimal and comma-decimal formats."""
    value = value.strip().replace(" ", "")
    if "," in value and "." in value:
        # Italian: 1.234,56
        value = value.replace(".", "").replace(",", ".")
    elif "," in value:
        value = value.replace(",", ".")
    return Decimal(value)


class SatispayParser(BaseParser):
    """Parser for Satispay CSV exports."""

    SOURCE_TYPE = "satispay"

    # ------------------------------------------------------------------ #
    # Detection
    # ------------------------------------------------------------------ #

    def detect(self, file_path: str, content: bytes) -> bool:
        """Detect Satispay CSV by checking for known column names."""
        if not content.strip():
            return False

        text = _decode_content(content)
        delimiter = _detect_delimiter(text)

        try:
            first_line = text.split("\n", 1)[0]
        except Exception:
            return False

        headers = {h.strip().lower() for h in first_line.split(delimiter)}

        return headers >= _REQUIRED_EN or headers >= _REQUIRED_IT

    # ------------------------------------------------------------------ #
    # Column mapping
    # ------------------------------------------------------------------ #

    def get_column_mapping(self) -> dict[str, str]:
        """Return canonical column mapping."""
        return {
            "ID": "metadata.id",
            "Date": "date",
            "Type": "type",
            "Amount": "amount",
            "Currency": "currency",
            "Name": "description",
            "Description": "description (appended)",
        }

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _resolve_columns(self, columns: pd.Index) -> dict[str, str]:
        """Map actual column names → canonical keys using aliases."""
        mapping: dict[str, str] = {}
        for col in columns:
            key = _COLUMN_ALIASES.get(col.strip().lower())
            if key:
                mapping[key] = col
        return mapping

    # ------------------------------------------------------------------ #
    # Parsing
    # ------------------------------------------------------------------ #

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Parse a Satispay CSV and return normalized transactions."""
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
        df.columns = df.columns.str.strip()

        col_map = self._resolve_columns(df.columns)

        transactions: list[RawTransaction] = []
        errors: list[str] = []

        for idx, row in df.iterrows():
            row_num = int(idx) + 2  # type: ignore[call-overload]
            try:
                # Date
                date_col = col_map.get("date")
                if date_col is None:
                    errors.append(f"Row {row_num}: missing date column")
                    continue
                parsed_date = _parse_date(str(row[date_col]))

                # Amount
                amount_col = col_map.get("amount")
                if amount_col is None:
                    errors.append(f"Row {row_num}: missing amount column")
                    continue
                amount = _parse_amount(str(row[amount_col]))

                # Currency
                currency_col = col_map.get("currency")
                currency = str(row[currency_col]).strip().upper() if currency_col else "EUR"

                # Description — combine Name + Description
                name_col = col_map.get("name")
                desc_col = col_map.get("description")
                parts = []
                if name_col:
                    parts.append(str(row[name_col]).strip())
                if desc_col and desc_col != name_col:
                    desc_val = str(row[desc_col]).strip()
                    if desc_val:
                        parts.append(desc_val)
                original_desc = " - ".join(parts) if parts else ""
                description = " ".join(original_desc.split())

                # Type
                type_col = col_map.get("type")
                raw_type = str(row[type_col]).strip().lower() if type_col else ""
                tx_type = _TYPE_MAP.get(raw_type, "expense" if amount < 0 else "income")

                # Metadata
                metadata: dict[str, str] = {}
                id_col = col_map.get("id")
                if id_col:
                    metadata["satispay_id"] = str(row[id_col]).strip()
                if type_col:
                    metadata["satispay_type"] = str(row[type_col]).strip()

                transactions.append(
                    RawTransaction(
                        date=parsed_date,
                        amount=amount,
                        currency=currency,
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
