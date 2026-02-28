"""Tests for ParserRegistry."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.parser.bank_csv import BankCSVParser
from app.services.parser.paypal import PayPalParser
from app.services.parser.registry import ParserRegistry
from app.services.parser.satispay import SatispayParser

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def registry() -> ParserRegistry:
    return ParserRegistry()


@pytest.fixture
def bank_content() -> bytes:
    return (FIXTURES / "bank_sample.csv").read_bytes()


@pytest.fixture
def satispay_content() -> bytes:
    return (FIXTURES / "satispay_sample.csv").read_bytes()


@pytest.fixture
def paypal_content() -> bytes:
    return (FIXTURES / "paypal_sample.csv").read_bytes()


# ------------------------------------------------------------------ #
# Auto-detection
# ------------------------------------------------------------------ #


class TestAutoDetect:
    def test_detect_bank_csv(self, registry: ParserRegistry, bank_content: bytes) -> None:
        parser = registry.detect("bank.csv", bank_content)
        assert isinstance(parser, BankCSVParser)

    def test_detect_satispay(self, registry: ParserRegistry, satispay_content: bytes) -> None:
        parser = registry.detect("satispay.csv", satispay_content)
        assert isinstance(parser, SatispayParser)

    def test_detect_paypal(self, registry: ParserRegistry, paypal_content: bytes) -> None:
        parser = registry.detect("paypal.csv", paypal_content)
        assert isinstance(parser, PayPalParser)

    def test_detect_unknown_returns_none(self, registry: ParserRegistry) -> None:
        content = b"foo,bar,baz\n1,2,3\n"
        assert registry.detect("unknown.csv", content) is None


# ------------------------------------------------------------------ #
# parse() dispatch
# ------------------------------------------------------------------ #


class TestParseDispatch:
    def test_parse_bank_csv(self, registry: ParserRegistry, bank_content: bytes) -> None:
        result = registry.parse("bank.csv", bank_content)
        assert result.source_type == "bank_csv"
        assert result.parsed_count == 6

    def test_parse_satispay(self, registry: ParserRegistry, satispay_content: bytes) -> None:
        result = registry.parse("satispay.csv", satispay_content)
        assert result.source_type == "satispay"
        assert result.parsed_count == 5

    def test_parse_paypal(self, registry: ParserRegistry, paypal_content: bytes) -> None:
        result = registry.parse("paypal.csv", paypal_content)
        assert result.source_type == "paypal"
        assert result.parsed_count == 5

    def test_unknown_raises_value_error(self, registry: ParserRegistry) -> None:
        content = b"foo,bar,baz\n1,2,3\n"
        with pytest.raises(ValueError, match="No parser found"):
            registry.parse("unknown.csv", content)
