"""Tests for the keyword dictionary."""

from __future__ import annotations

from app.seeds import SYSTEM_CATEGORIES
from app.services.categorization.keywords import KEYWORD_MAP


def _all_category_name_keys() -> set[str]:
    """Collect every valid name_key from SYSTEM_CATEGORIES (parents + children)."""
    keys: set[str] = set()
    for name_key, _icon, _color, _is_income, children in SYSTEM_CATEGORIES:
        keys.add(name_key)
        for child_name, _ci, _cc in children:
            keys.add(child_name)
    return keys


class TestKeywordMap:
    def test_not_empty(self) -> None:
        assert len(KEYWORD_MAP) > 0

    def test_at_least_80_entries(self) -> None:
        assert len(KEYWORD_MAP) >= 80

    def test_all_values_are_valid_categories(self) -> None:
        valid = _all_category_name_keys()
        for keyword, category in KEYWORD_MAP.items():
            assert category in valid, f"Keyword {keyword!r} maps to unknown category {category!r}"

    def test_all_keys_are_lowercase(self) -> None:
        for keyword in KEYWORD_MAP:
            assert keyword == keyword.lower(), f"Keyword {keyword!r} is not lowercase"

    def test_specific_mappings(self) -> None:
        assert KEYWORD_MAP["esselunga"] == "Supermercato"
        assert KEYWORD_MAP["netflix"] == "Abbonamenti"
        assert KEYWORD_MAP["farmacia"] == "Farmacia"
        assert KEYWORD_MAP["stipendio"] == "Stipendio"
        assert KEYWORD_MAP["rimborso"] == "Rimborsi"
        assert KEYWORD_MAP["amazon prime"] == "Abbonamenti"
