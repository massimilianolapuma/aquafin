"""Tests for the bank-pattern regex rules."""

from __future__ import annotations

import re

from app.services.categorization.patterns import PATTERN_RULES


class TestPatternRules:
    def test_not_empty(self) -> None:
        assert len(PATTERN_RULES) > 0

    def test_at_least_15_patterns(self) -> None:
        assert len(PATTERN_RULES) >= 15

    def test_all_entries_are_tuples(self) -> None:
        for entry in PATTERN_RULES:
            assert isinstance(entry, tuple) and len(entry) == 3  # noqa: PT018
            pattern, category, confidence = entry
            assert isinstance(pattern, re.Pattern)
            assert isinstance(category, str)
            assert 0.0 <= confidence <= 1.0

    def test_addebito_sdd_enel(self) -> None:
        """ADDEBITO SDD with utility provider name should match Utenze."""
        matched = _first_match("ADDEBITO SDD FATTURA ENEL SERVIZIO ELETTRICO")
        assert matched is not None
        assert matched[1] == "Utenze"

    def test_addebito_sdd_generic(self) -> None:
        """Generic ADDEBITO SDD should match Altro spese."""
        matched = _first_match("ADDEBITO SDD SCONOSCIUTO SRL")
        assert matched is not None
        assert matched[1] == "Altro spese"

    def test_bonifico_stipendio(self) -> None:
        matched = _first_match("BONIFICO SEPA STIPENDIO FEBBRAIO 2025")
        assert matched is not None
        assert matched[1] == "Stipendio"
        assert matched[2] == 0.9

    def test_pagamento_pos(self) -> None:
        matched = _first_match("PAGAMENTO POS 01/01 SHOP GENERICO")
        assert matched is not None
        assert matched[1] == "Altro spese"

    def test_prelievo_bancomat(self) -> None:
        matched = _first_match("PRELIEVO BANCOMAT 200 EUR")
        assert matched is not None
        assert matched[1] == "Altro spese"

    def test_rata_mutuo(self) -> None:
        matched = _first_match("RATA MUTUO IPOTECARIO N.12345")
        assert matched is not None
        assert matched[1] == "Affitto/Mutuo"

    def test_f24(self) -> None:
        matched = _first_match("PAGAMENTO F24 SEMPLIFICATO")
        assert matched is not None
        assert matched[1] == "Tasse"

    def test_accredito_competenze(self) -> None:
        matched = _first_match("ACCREDITO COMPETENZE TRIMESTRI")
        assert matched is not None
        assert matched[1] == "Interessi"

    def test_assicurazione_auto(self) -> None:
        matched = _first_match("POLIZZA AUTO RCA 2025")
        assert matched is not None
        assert matched[1] == "Assicurazione auto"


def _first_match(
    description: str,
) -> tuple[re.Pattern[str], str, float] | None:
    """Return the first matching pattern rule or None."""
    for pattern, category, confidence in PATTERN_RULES:
        if pattern.search(description):
            return (pattern, category, confidence)
    return None
