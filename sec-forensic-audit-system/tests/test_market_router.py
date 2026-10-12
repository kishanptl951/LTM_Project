"""
Tests for Market Router: market detection, ticker normalization, and currency formatting.
"""
import pytest
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.market_router import (
    detect_market, normalize_ticker, format_value, format_indian_value,
    get_currency_symbol, get_currency_code,
)


class TestDetectMarket:
    """Tests for detect_market() function."""

    def test_nse_suffix_detected_as_india(self):
        assert detect_market("RELIANCE.NS") == "INDIA"

    def test_bse_suffix_detected_as_india(self):
        assert detect_market("TCS.BO") == "INDIA"

    def test_us_ticker_detected_as_us(self):
        assert detect_market("AAPL") == "US"

    def test_known_indian_base_ticker(self):
        """Known Indian ticker without suffix should still detect as India."""
        assert detect_market("RELIANCE") == "INDIA"

    def test_known_us_ticker(self):
        assert detect_market("MSFT") == "US"

    def test_case_insensitive(self):
        assert detect_market("reliance.ns") == "INDIA"
        assert detect_market("aapl") == "US"

    def test_unknown_ticker_defaults_to_us(self):
        """Unknown tickers default to US market."""
        assert detect_market("XYZUNKNOWN") == "US"


class TestNormalizeTicker:
    """Tests for normalize_ticker() function."""

    def test_indian_ticker_gets_ns_suffix(self):
        assert normalize_ticker("RELIANCE", "INDIA") == "RELIANCE.NS"

    def test_indian_ticker_keeps_existing_ns(self):
        assert normalize_ticker("TCS.NS", "INDIA") == "TCS.NS"

    def test_indian_ticker_keeps_bo_suffix(self):
        assert normalize_ticker("INFY.BO", "INDIA") == "INFY.BO"

    def test_us_ticker_stays_clean(self):
        assert normalize_ticker("AAPL", "US") == "AAPL"

    def test_auto_detect_market_when_none(self):
        """When market is None, auto-detects and normalizes accordingly."""
        result = normalize_ticker("RELIANCE.NS")
        assert result == "RELIANCE.NS"


class TestCurrencyFormatting:
    """Tests for currency formatting utilities."""

    def test_get_currency_symbol_us(self):
        assert get_currency_symbol("US") == "$"

    def test_get_currency_symbol_india(self):
        assert get_currency_symbol("INDIA") == "₹"

    def test_get_currency_code_us(self):
        assert get_currency_code("US") == "USD"

    def test_get_currency_code_india(self):
        assert get_currency_code("INDIA") == "INR"

    def test_format_value_us(self):
        result = format_value(254940000000, "US")
        assert "$" in result
        assert "254,940,000,000" in result

    def test_format_value_india_crores(self):
        result = format_value(954230000000, "INDIA")
        assert "₹" in result
        assert "Cr" in result

    def test_format_indian_value_large(self):
        result = format_indian_value(100000000000)  # 10,000 Cr
        assert "₹" in result
        assert "Cr" in result

    def test_format_indian_value_small(self):
        result = format_indian_value(500000)  # 5 Lakhs
        assert "₹" in result
        assert "L" in result
