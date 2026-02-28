"""Regex patterns for Italian bank transaction categorization.

Each entry is a tuple of ``(compiled_regex, category_name_key, confidence)``.
Patterns are checked in order; the first match wins.
"""

from __future__ import annotations

import re

# List of (compiled_regex, category_name_key, confidence)
PATTERN_RULES: list[tuple[re.Pattern[str], str, float]] = [
    # ── Salary / payroll ────────────────────────────────────────────────
    (
        re.compile(
            r"BONIFICO.*(STIPENDIO|RETRIBUZIONE|SALARIO|EMOLUMENT)",
            re.IGNORECASE,
        ),
        "Stipendio",
        0.9,
    ),
    # ── Rent / mortgage ─────────────────────────────────────────────────
    (
        re.compile(
            r"BONIFICO.*(AFFITTO|CANONE\s+LOCAZIONE)",
            re.IGNORECASE,
        ),
        "Affitto/Mutuo",
        0.85,
    ),
    (
        re.compile(r"RATA\s+MUTUO|ADDEBITO\s+MUTUO", re.IGNORECASE),
        "Affitto/Mutuo",
        0.9,
    ),
    # ── Utility direct-debits (SDD) ─────────────────────────────────────
    (
        re.compile(
            r"ADDEBITO\s+SDD.*(ENEL|IREN|A2A|HERA|ACEA|SORGENIA|EDISON|ITALGAS)",
            re.IGNORECASE,
        ),
        "Utenze",
        0.85,
    ),
    (
        re.compile(
            r"ADDEBITO\s+SDD.*(TIM|VODAFONE|WIND|ILIAD|FASTWEB)",
            re.IGNORECASE,
        ),
        "Telefonia",
        0.85,
    ),
    (
        re.compile(r"ADDEBITO\s+SDD", re.IGNORECASE),
        "Altro spese",
        0.5,
    ),
    # ── Bank transfers (generic) ────────────────────────────────────────
    (
        re.compile(r"BONIFICO\s+(DA|IN\s+FAVORE)", re.IGNORECASE),
        "Altro spese",
        0.3,
    ),
    # ── POS payments ────────────────────────────────────────────────────
    (
        re.compile(r"PAGAMENTO\s+POS", re.IGNORECASE),
        "Altro spese",
        0.3,
    ),
    # ── ATM withdrawals ─────────────────────────────────────────────────
    (
        re.compile(r"PRELIEVO\s+(BANCOMAT|ATM)", re.IGNORECASE),
        "Altro spese",
        0.6,
    ),
    # ── Internal transfers ──────────────────────────────────────────────
    (
        re.compile(r"GIROCONTO", re.IGNORECASE),
        "Altro spese",
        0.3,
    ),
    # ── Interest income ─────────────────────────────────────────────────
    (
        re.compile(
            r"ACCREDITO\s+COMPETENZE|INTERESSI\s+CREDITOR",
            re.IGNORECASE,
        ),
        "Interessi",
        0.85,
    ),
    # ── Tolls / highway ─────────────────────────────────────────────────
    (
        re.compile(r"PEDAGG|TELEPASS", re.IGNORECASE),
        "Parcheggio",
        0.8,
    ),
    # ── Insurance ───────────────────────────────────────────────────────
    (
        re.compile(
            r"ASSICURAZION.*AUTO|RCA|POLIZZA.*AUTO",
            re.IGNORECASE,
        ),
        "Assicurazione auto",
        0.85,
    ),
    (
        re.compile(
            r"ASSICURAZION.*CASA|POLIZZA.*CASA",
            re.IGNORECASE,
        ),
        "Assicurazione casa",
        0.85,
    ),
    # ── Taxes ───────────────────────────────────────────────────────────
    (
        re.compile(r"F24|TASSE|TRIBUT|IRPEF|IMU|TASI|TARI", re.IGNORECASE),
        "Tasse",
        0.85,
    ),
    # ── Refund ──────────────────────────────────────────────────────────
    (
        re.compile(r"RIMBORSO|STORNO", re.IGNORECASE),
        "Rimborsi",
        0.7,
    ),
    # ── Dividends / coupons ─────────────────────────────────────────────
    (
        re.compile(r"DIVIDENDO|CEDOLA|STACCO\s+CEDOLA", re.IGNORECASE),
        "Dividendi",
        0.85,
    ),
]
