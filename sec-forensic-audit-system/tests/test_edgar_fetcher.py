"""
Unit tests for EdgarFetcher module.
"""
import pytest
from pathlib import Path
from src.ingestion.edgar_fetcher import EdgarFetcher


def test_edgar_fetcher_initialization(tmp_path):
    fetcher = EdgarFetcher(output_dir=tmp_path)
    assert fetcher.output_dir == tmp_path


def test_edgar_fetcher_caching(tmp_path, monkeypatch):
    fetcher = EdgarFetcher(output_dir=tmp_path)
    ticker = "TEST"
    
    ticker_dir = tmp_path / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)
    facts_file = ticker_dir / "xbrl_facts.json"
    
    # Pre-populate cache
    cached_data = {"ticker": "TEST", "name": "Test Company Inc.", "facts": [{"fact": "sample"}]}
    import json
    with open(facts_file, "w", encoding="utf-8") as f:
        json.dump(cached_data, f)
        
    result = fetcher.fetch_company_facts(ticker)
    assert result["ticker"] == "TEST"
    assert result["name"] == "Test Company Inc."
    assert len(result["facts"]) == 1
