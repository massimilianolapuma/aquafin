"""PayPal CSV export parser."""
from __future__ import annotations

import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import pandas as pd

from .base import BaseParser, ParseResult, RawTransaction

# Required column sets (lowercase for matching)
_REQUIRED_EN = {"date", "name", "type", "status", "currency", "gross"}
_REQUIRED_IT = {"data", "nome", "tipo", "stato", "valuta", "lordo"}

# Column aliases → canonical keys
_COLUMN_ALIASES: dict[str, str] = {
    # English
    "date": "date",
    "name": "name",
    "type": "type",
    "status": "status",
    "currency": "currency",
    "gross": "gross",
    "fee": "fee",
    "net": "net",
    # Italian
    "data": "date",
    "nome": "name",
    "tipo": "type",
    "stato": "status",
    "valuta": "currency",
    "lordo": "gross",
    "tariffa": "fee",
    "netto": "net",
}

# PayPal type → transaction type
_TYPE_MAP: dict[str, str] = {
    "payment": "expense",
    "refund": "income",
    "transfer": "transfer",
    "withdrawal": "transfer",
    "deposit": "income",
    "currency conversion": "transfer",
    # Italian variants
    "pagamento": "expense",
    "rimborso": "income",
    "trasferimento": "transfer",
    "prelievo": "transfer",
    "deposito": "income",
    "conversione valuta": "transfer",
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
    """Parse date in multiple formats (mm/dd/yyyy is PayPal default, plus ISO and Italian)."""
    value = value.strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {value!r}")


def _parse_amount(value: str) -> Decimal:
    """Parse amount handling both dot-decimal and comma-decimal formats."""
    value = value.strip().replace(" ", "")
    if not value:
        return Decimal("0")
    if "," in value and "." in value:
        # Determine which is the decimal separator (rightmost wins)
        if value.rindex(",") > value.rindex("."):
            # comma-decimal: 1.234,56
            value = value.replace(".", "").replace(",", ".")
        # else: dot-decimal with thousands comma: 1,234.56 — just remove commas
        else:
            value = value.replace(",", "")
    elif "," in value:
        value = value.replace(",", ".")
    return Decimal(value)


class PayPalParser(BaseParser):
    """Parser for PayPal CSV exports."""

    SOURCE_TYPE = "paypal"

    # ------------------------------------------------------------------ #
    # Detection
    # ------------------------------------------------------------------ #

    def detect(self, file_path: str, content: bytes) -> bool:
        """Detect PayPal CSV by checking for known column names."""
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
            "Date": "date",
            "Name": "description",
            "Gross": "amount",
            "Currency": "currency",
            "Fee": "metadata.fee",
            "Net": "metadata.net",
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
        """Parse a PayPal CSV and return normalized transactions."""
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
            row_num = int(idx) + 2
            try:
                # Date
                date_col = col_map.get("date")
                if date_col is None:
                    errors.append(f"Row {row_num}: missing date column")
                    continue
                parsed_date = _parse_date(str(row[date_col]))

                # Amount (use Gross, not Net)
                gross_col = col_map.get("gross")
                if gross_col is None:
                    errors.append(f"Row {row_num}: missing gross/amount column")
                    continue
                amount = _parse_amount(str(row[gross_col]))

                # Currency
                currency_col = col_map.get("currency")
                currency = str(row[currency_col]).strip().upper() if currency_col else "EUR"

                # Description
                name_col = col_map.get("name")
                original_desc = str(row[name_col]).strip() if name_col else ""
                description = " ".join(original_desc.split())

                # Type
                type_col = col_map.get("type")
                raw_type = str(row[type_col]).strip().lower() if type_col else ""
                tx_type = _TYPE_MAP.get(raw_type, "expense" if amount < 0 else "income")

                # Metadata (fee, net, status)
                metadata: dict = {}
                fee_col = col_map.get("fee")
                if fee_col:
                    fee_str = str(row[fee_col]).strip()
                    if fee_str:
                        metadata["fee"] = str(_parse_amount(fee_str))
                net_col = col_map.get("net")
                if net_col:
                    net_str = str(row[net_col]).strip()
                    if net_str:
                        metadata["net"] = str(_parse_amount(net_str))
                status_col = col_map.get("status")
                if status_col:
                    metadata["status"] = str(row[status_col]).strip()
                if type_col:
                    metadata["paypal_type"] = str(row[type_col]).strip()

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
