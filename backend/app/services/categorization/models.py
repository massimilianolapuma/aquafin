"""Data models for categorization results."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class CategorizationResult:
    """Result of categorizing a single transaction."""

    category_name: str  # e.g., "Supermercato"
    confidence: float  # 0.0 – 1.0
    matched_by: str  # "user_rule" | "keyword" | "pattern" | "fallback"
    rule_id: str | None = None  # UUID of matched user rule, if any


@dataclass
class CategorizedTransaction:
    """Transaction with categorization result attached."""

    date: date
    amount: Decimal
    currency: str
    description: str
    original_description: str
    type: str
    metadata: dict
    categorization: CategorizationResult
