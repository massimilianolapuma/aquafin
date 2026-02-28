"""Parser registry with auto-detection."""
from __future__ import annotations

from .bank_csv import BankCSVParser
from .base import BaseParser, ParseResult
from .paypal import PayPalParser
from .pdf_parser import PDFParser
from .satispay import SatispayParser


class ParserRegistry:
    """Registry of all available parsers with auto-detection."""

    def __init__(self) -> None:
        self._parsers: list[BaseParser] = [
            BankCSVParser(),
            SatispayParser(),
            PayPalParser(),
            PDFParser(),
        ]

    def detect(self, file_path: str, content: bytes) -> BaseParser | None:
        """Try each parser's detect() and return the first match."""
        for parser in self._parsers:
            if parser.detect(file_path, content):
                return parser
        return None

    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Auto-detect and parse. Raises ValueError if no parser matches."""
        parser = self.detect(file_path, content)
        if parser is None:
            raise ValueError(f"No parser found for file: {file_path}")
        return parser.parse(file_path, content)
