"""
Tests for NSE Fetcher: validates yfinance data fetching and normalization for Indian stocks.
Uses mocking to avoid actual API calls during testing.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.nse_fetcher import NSEFetcher


class TestNSEFetcherTickerNormalization:
    """Tests for ticker normalization logic."""

    def setup_method(self):
        self.fetcher = NSEFetcher(output_dir=Path("tests/temp_test_data"))

    def test_normalize_plain_ticker(self):
        assert self.fetcher._normalize_ticker("RELIANCE") == "RELIANCE.NS"

    def test_normalize_already_ns(self):
        assert self.fetcher._normalize_ticker("TCS.NS") == "TCS.NS"

    def test_normalize_bo_suffix(self):
        assert self.fetcher._normalize_ticker("INFY.BO") == "INFY.BO"

    def test_normalize_lowercase(self):
        result = self.fetcher._normalize_ticker("reliance")
        assert result == "RELIANCE.NS"

    def test_get_base_ticker(self):
        assert self.fetcher._get_base_ticker("RELIANCE.NS") == "RELIANCE"
        assert self.fetcher._get_base_ticker("TCS.BO") == "TCS"
        assert self.fetcher._get_base_ticker("HDFCBANK") == "HDFCBANK"


class TestNSEFetcherFactExtraction:
    """Tests for financial statement DataFrame to fact record conversion."""

    def setup_method(self):
        self.fetcher = NSEFetcher(output_dir=Path("tests/temp_test_data"))

    def test_extract_facts_from_empty_df(self):
        """Empty DataFrame should return empty list."""
        facts = self.fetcher._extract_facts_from_df(
            pd.DataFrame(), "RELIANCE.NS", "RELIANCE", "annual", "income"
        )
        assert facts == []

    def test_extract_facts_from_none_df(self):
        """None DataFrame should return empty list."""
        facts = self.fetcher._extract_facts_from_df(
            None, "RELIANCE.NS", "RELIANCE", "annual", "income"
        )
        assert facts == []

    def test_extract_facts_from_valid_df(self):
        """Valid DataFrame should produce fact records with correct structure."""
        # Create a mock yfinance-style DataFrame
        dates = pd.to_datetime(["2024-03-31", "2023-03-31"])
        df = pd.DataFrame(
            {dates[0]: [954230000000.0, 73670000000.0], dates[1]: [850000000000.0, 65000000000.0]},
            index=["Total Revenue", "Net Income"]
        )

        facts = self.fetcher._extract_facts_from_df(
            df, "RELIANCE.NS", "RELIANCE", "annual", "income"
        )

        assert len(facts) == 4  # 2 concepts × 2 dates
        
        # Check structure of first fact
        first_fact = facts[0]
        assert first_fact["ticker"] == "RELIANCE.NS"
        assert first_fact["unit"] == "INR"
        assert first_fact["market"] == "INDIA"
        assert first_fact["statement_type"] == "income"
        assert first_fact["concept"] == "Total Revenue"
        assert first_fact["val"] == 954230000000.0
        assert first_fact["fiscal_period"] == "FY"  # annual

    def test_extract_facts_quarterly(self):
        """Quarterly data should have correct fiscal period mapping."""
        dates = pd.to_datetime(["2024-06-30"])  # Apr-Jun = Q1 in Indian FY
        df = pd.DataFrame(
            {dates[0]: [250000000000.0]},
            index=["Total Revenue"]
        )

        facts = self.fetcher._extract_facts_from_df(
            df, "RELIANCE.NS", "RELIANCE", "quarterly", "income"
        )

        assert len(facts) == 1
        assert facts[0]["fiscal_period"] == "Q1"
        assert facts[0]["form"] == "quarterly"

    def test_nan_values_skipped(self):
        """NaN values should be skipped in fact extraction."""
        dates = pd.to_datetime(["2024-03-31"])
        df = pd.DataFrame(
            {dates[0]: [float("nan")]},
            index=["Total Revenue"]
        )

        facts = self.fetcher._extract_facts_from_df(
            df, "RELIANCE.NS", "RELIANCE", "annual", "income"
        )

        assert len(facts) == 0

    def test_ingest_to_duckdb_success(self):
        """Test successful fetch and ingestion into DuckDB engine."""
        mock_engine = MagicMock()
        mock_engine.ingest_facts.return_value = 5

        with patch.object(self.fetcher, "fetch_company_facts", return_value={"facts": [{"val": 100}]}):
            result = self.fetcher.ingest_to_duckdb("RELIANCE.NS", mock_engine)
            assert result is True
            mock_engine.ingest_facts.assert_called_once()

    def test_ingest_to_duckdb_empty_facts(self):
        """Test ingestion failure when no facts are returned."""
        mock_engine = MagicMock()

        with patch.object(self.fetcher, "fetch_company_facts", return_value={"facts": []}):
            result = self.fetcher.ingest_to_duckdb("RELIANCE.NS", mock_engine)
            assert result is False
            mock_engine.ingest_facts.assert_not_called()

    def test_ingest_to_duckdb_exception_handling(self):
        """Test that exceptions during ingestion are handled gracefully."""
        mock_engine = MagicMock()
        mock_engine.ingest_facts.side_effect = RuntimeError("Database error")

        with patch.object(self.fetcher, "fetch_company_facts", return_value={"facts": [{"val": 100}]}):
            result = self.fetcher.ingest_to_duckdb("RELIANCE.NS", mock_engine)
            assert result is False
