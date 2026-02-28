"""Tests for the rule-based categorization engine."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.services.categorization.engine import CategorizationEngine, UserRule
from app.services.parser.base import RawTransaction

# ── helpers ─────────────────────────────────────────────────────────────────


def _make_tx(
    description: str,
    tx_type: str = "expense",
    amount: Decimal | None = None,
) -> RawTransaction:
    """Create a minimal RawTransaction for testing."""
    return RawTransaction(
        date=date(2025, 6, 1),
        amount=amount or Decimal("10.00"),
        currency="EUR",
        description=description,
        original_description=description,
        type=tx_type,
    )


# ── user rule matching ──────────────────────────────────────────────────────


class TestUserRuleContains:
    def test_contains_match(self) -> None:
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="r1",
                    pattern="esselunga",
                    match_type="contains",
                    category_name="Supermercato",
                ),
            ]
        )
        result = engine.categorize(_make_tx("Pagamento POS Esselunga Milano"))
        assert result.categorization.category_name == "Supermercato"
        assert result.categorization.confidence == 1.0
        assert result.categorization.matched_by == "user_rule"
        assert result.categorization.rule_id == "r1"


class TestUserRuleExact:
    def test_exact_match(self) -> None:
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="r2",
                    pattern="AFFITTO MENSILE",
                    match_type="exact",
                    category_name="Affitto/Mutuo",
                ),
            ]
        )
        result = engine.categorize(_make_tx("Affitto Mensile"))
        assert result.categorization.category_name == "Affitto/Mutuo"
        assert result.categorization.matched_by == "user_rule"

    def test_exact_no_match_on_substring(self) -> None:
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="r2",
                    pattern="AFFITTO",
                    match_type="exact",
                    category_name="Affitto/Mutuo",
                ),
            ]
        )
        result = engine.categorize(_make_tx("AFFITTO MENSILE"))
        # "exact" should NOT match because descriptions differ
        assert result.categorization.matched_by != "user_rule"


class TestUserRuleStartsWith:
    def test_starts_with_match(self) -> None:
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="r3",
                    pattern="PAGAMENTO POS",
                    match_type="starts_with",
                    category_name="Altro spese",
                ),
            ]
        )
        result = engine.categorize(_make_tx("PAGAMENTO POS CONAD"))
        assert result.categorization.category_name == "Altro spese"
        assert result.categorization.matched_by == "user_rule"


class TestUserRuleRegex:
    def test_regex_match(self) -> None:
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="r4",
                    pattern=r"RATA\s+MUTUO\s+\d+",
                    match_type="regex",
                    category_name="Affitto/Mutuo",
                ),
            ]
        )
        result = engine.categorize(_make_tx("Rata Mutuo 12345"))
        assert result.categorization.category_name == "Affitto/Mutuo"
        assert result.categorization.matched_by == "user_rule"

    def test_invalid_regex_does_not_crash(self) -> None:
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="r5",
                    pattern=r"[invalid",
                    match_type="regex",
                    category_name="Tasse",
                ),
            ]
        )
        result = engine.categorize(_make_tx("anything"))
        # Should not crash — just not match; falls through to fallback
        assert result.categorization.matched_by in ("keyword", "pattern", "fallback")


class TestUserRulePriority:
    def test_higher_priority_wins(self) -> None:
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="low",
                    pattern="esselunga",
                    match_type="contains",
                    category_name="Ristorante",
                    priority=1,
                ),
                UserRule(
                    id="high",
                    pattern="esselunga",
                    match_type="contains",
                    category_name="Supermercato",
                    priority=10,
                ),
            ]
        )
        result = engine.categorize(_make_tx("ESSELUNGA"))
        assert result.categorization.category_name == "Supermercato"
        assert result.categorization.rule_id == "high"


# ── keyword matching ────────────────────────────────────────────────────────


class TestKeywordMatching:
    def test_keyword_confidence(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("Pagamento POS ESSELUNGA"))
        assert result.categorization.matched_by == "keyword"
        assert result.categorization.confidence == 0.7

    @pytest.mark.parametrize(
        "description, expected_category",
        [
            ("Pagamento POS Esselunga Milano", "Supermercato"),
            ("Addebito Netflix mensile", "Abbonamenti"),
            ("Farmacia Comunale", "Farmacia"),
            ("Booking.com prenotazione", "Viaggi"),
            ("Vodafone ricarica", "Telefonia"),
            ("MediaWorld acquisto", "Elettronica"),
            ("Decathlon sport", "Abbigliamento"),
            ("Conad spesa settimanale", "Supermercato"),
            ("Deliveroo ordine cibo", "Delivery"),
            ("IKEA acquisto mobili", "Casa e arredo"),
        ],
    )
    def test_specific_merchants(self, description: str, expected_category: str) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx(description))
        assert result.categorization.category_name == expected_category

    def test_case_insensitive_keyword(self) -> None:
        engine = CategorizationEngine()
        r1 = engine.categorize(_make_tx("ESSELUNGA MILANO"))
        r2 = engine.categorize(_make_tx("esselunga milano"))
        assert r1.categorization.category_name == r2.categorization.category_name

    def test_longer_keyword_takes_precedence(self) -> None:
        """'amazon prime' should match Abbonamenti, not Elettronica."""
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("Addebito Amazon Prime Video"))
        assert result.categorization.category_name == "Abbonamenti"


# ── pattern matching ────────────────────────────────────────────────────────


class TestPatternMatching:
    def test_pattern_matched_by(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("GIROCONTO TRA CONTI CORRENTI"))
        assert result.categorization.matched_by == "pattern"

    def test_bonifico_stipendio(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("BONIFICO SEPA EMOLUMENTI MESE CORRENTE"))
        assert result.categorization.category_name == "Stipendio"
        assert result.categorization.confidence == 0.9

    def test_addebito_sdd(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("ADDEBITO SDD ENEL SERVIZIO ELETTRICO"))
        assert result.categorization.category_name == "Utenze"

    def test_rata_mutuo(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("RATA MUTUO IPOTECARIO"))
        assert result.categorization.category_name == "Affitto/Mutuo"

    def test_pagamento_pos_pattern(self) -> None:
        engine = CategorizationEngine()
        # A generic POS description without any keyword match
        result = engine.categorize(_make_tx("PAGAMENTO POS 12345 GENERICO"))
        assert result.categorization.category_name == "Altro spese"

    def test_f24_taxes(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("PAGAMENTO F24 SEMPLIFICATO"))
        assert result.categorization.category_name == "Tasse"


# ── fallback ────────────────────────────────────────────────────────────────


class TestFallback:
    def test_expense_fallback(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("XYZNOMATCH1234567890", tx_type="expense"))
        assert result.categorization.category_name == "Altro spese"
        assert result.categorization.confidence == 0.0
        assert result.categorization.matched_by == "fallback"

    def test_income_fallback(self) -> None:
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("XYZNOMATCH1234567890", tx_type="income"))
        assert result.categorization.category_name == "Altro entrate"
        assert result.categorization.confidence == 0.0
        assert result.categorization.matched_by == "fallback"


# ── pipeline priority ──────────────────────────────────────────────────────


class TestPipelinePriority:
    def test_user_rule_beats_keyword(self) -> None:
        """When both a user rule and keyword would match, user rule wins."""
        engine = CategorizationEngine(
            user_rules=[
                UserRule(
                    id="custom",
                    pattern="netflix",
                    match_type="contains",
                    category_name="Svago",
                ),
            ]
        )
        result = engine.categorize(_make_tx("NETFLIX MENSILE"))
        assert result.categorization.matched_by == "user_rule"
        assert result.categorization.category_name == "Svago"

    def test_keyword_beats_pattern(self) -> None:
        """Keyword match should take precedence over pattern match."""
        engine = CategorizationEngine()
        # "ADDEBITO SDD ENEL" matches both keyword (enel→Utenze) and pattern
        result = engine.categorize(_make_tx("Pagamento enel energia"))
        assert result.categorization.matched_by == "keyword"

    def test_pattern_beats_fallback(self) -> None:
        """Pattern match should prevent fallback."""
        engine = CategorizationEngine()
        result = engine.categorize(_make_tx("PRELIEVO BANCOMAT 200 EUR"))
        assert result.categorization.matched_by == "pattern"


# ── batch ───────────────────────────────────────────────────────────────────


class TestBatch:
    def test_categorize_batch(self) -> None:
        engine = CategorizationEngine()
        txs = [
            _make_tx("ESSELUNGA SPESA"),
            _make_tx("XYZNOMATCH999", tx_type="income"),
            _make_tx("RATA MUTUO IPOTECARIO"),
        ]
        results = engine.categorize_batch(txs)
        assert len(results) == 3
        assert results[0].categorization.category_name == "Supermercato"
        assert results[1].categorization.category_name == "Altro entrate"
        assert results[2].categorization.category_name == "Affitto/Mutuo"


# ── CategorizedTransaction fields ──────────────────────────────────────────


class TestCategorizedTransactionFields:
    def test_fields_propagated(self) -> None:
        tx = _make_tx("ESSELUNGA", amount=Decimal("42.50"))
        engine = CategorizationEngine()
        result = engine.categorize(tx)
        assert result.date == date(2025, 6, 1)
        assert result.amount == Decimal("42.50")
        assert result.currency == "EUR"
        assert result.description == "ESSELUNGA"
        assert result.original_description == "ESSELUNGA"
        assert result.type == "expense"
