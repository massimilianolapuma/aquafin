"""Rule-based categorization engine."""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.parser.base import RawTransaction

from .keywords import KEYWORD_MAP
from .models import CategorizedTransaction, CategorizationResult
from .patterns import PATTERN_RULES


@dataclass
class UserRule:
    """Simplified representation of a user's categorization rule for the engine.

    This is **not** the SQLAlchemy ``CategorizationRule`` model — it is a plain
    dataclass so the engine stays DB-agnostic and testable in isolation.
    """

    id: str
    pattern: str
    match_type: str  # "contains" | "exact" | "regex" | "starts_with"
    category_name: str
    priority: int = 0


class CategorizationEngine:
    """Pipeline: user_rules → keywords → patterns → fallback."""

    def __init__(self, user_rules: list[UserRule] | None = None) -> None:
        self._user_rules = sorted(
            user_rules or [],
            key=lambda r: r.priority,
            reverse=True,  # highest priority first
        )

    # ── public API ──────────────────────────────────────────────────────

    def categorize(self, transaction: RawTransaction) -> CategorizedTransaction:
        """Run the full pipeline and return a categorized transaction."""
        result = (
            self._try_user_rules(transaction.description)
            or self._try_keywords(transaction.description)
            or self._try_patterns(transaction.description)
            or self._fallback(transaction.type)
        )
        return CategorizedTransaction(
            date=transaction.date,
            amount=transaction.amount,
            currency=transaction.currency,
            description=transaction.description,
            original_description=transaction.original_description,
            type=transaction.type,
            metadata=transaction.metadata,
            categorization=result,
        )

    def categorize_batch(
        self, transactions: list[RawTransaction]
    ) -> list[CategorizedTransaction]:
        """Categorize a list of transactions."""
        return [self.categorize(t) for t in transactions]

    # ── private helpers ─────────────────────────────────────────────────

    def _try_user_rules(self, description: str) -> CategorizationResult | None:
        desc_lower = description.lower()
        for rule in self._user_rules:
            if self._match_rule(desc_lower, rule):
                return CategorizationResult(
                    category_name=rule.category_name,
                    confidence=1.0,
                    matched_by="user_rule",
                    rule_id=rule.id,
                )
        return None

    @staticmethod
    def _match_rule(desc_lower: str, rule: UserRule) -> bool:
        """Apply a single user rule against the lowered description."""
        pattern_lower = rule.pattern.lower()
        if rule.match_type == "contains":
            return pattern_lower in desc_lower
        if rule.match_type == "exact":
            return desc_lower == pattern_lower
        if rule.match_type == "starts_with":
            return desc_lower.startswith(pattern_lower)
        if rule.match_type == "regex":
            try:
                return bool(re.search(rule.pattern, desc_lower, re.IGNORECASE))
            except re.error:
                return False
        return False

    @staticmethod
    def _try_keywords(description: str) -> CategorizationResult | None:
        """Try to match the description against the keyword dictionary.

        Keywords are tried longest-first so more-specific entries win.
        """
        desc_lower = description.lower()
        for keyword in sorted(KEYWORD_MAP, key=len, reverse=True):
            if keyword in desc_lower:
                return CategorizationResult(
                    category_name=KEYWORD_MAP[keyword],
                    confidence=0.7,
                    matched_by="keyword",
                )
        return None

    @staticmethod
    def _try_patterns(description: str) -> CategorizationResult | None:
        """Try to match the description against bank-pattern regexes."""
        for pattern, category_name, confidence in PATTERN_RULES:
            if pattern.search(description):
                return CategorizationResult(
                    category_name=category_name,
                    confidence=confidence,
                    matched_by="pattern",
                )
        return None

    @staticmethod
    def _fallback(transaction_type: str) -> CategorizationResult:
        """Return a low-confidence fallback category."""
        if transaction_type == "income":
            return CategorizationResult(
                category_name="Altro entrate",
                confidence=0.0,
                matched_by="fallback",
            )
        return CategorizationResult(
            category_name="Altro spese",
            confidence=0.0,
            matched_by="fallback",
        )
