"""Base parser protocol and shared data structures."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass
class RawTransaction:
    """Normalized transaction extracted from a file."""

    date: date
    amount: Decimal
    currency: str  # ISO 4217
    description: str
    original_description: str
    type: str  # "income" | "expense" | "transfer"
    metadata: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    """Result of parsing a file."""

    transactions: list[RawTransaction]
    source_type: str  # "bank_csv", "satispay", "paypal", "pdf"
    row_count: int
    parsed_count: int
    errors: list[str] = field(default_factory=list)


class BaseParser(ABC):
    """Abstract base class for all file parsers."""

    @abstractmethod
    def detect(self, file_path: str, content: bytes) -> bool:
        """Return True if this parser recognizes the file format."""
        ...

    @abstractmethod
    def parse(self, file_path: str, content: bytes) -> ParseResult:
        """Parse the file and return normalized transactions."""
        ...

    @abstractmethod
    def get_column_mapping(self) -> dict[str, str]:
        """Map source columns → RawTransaction fields."""
        ...
