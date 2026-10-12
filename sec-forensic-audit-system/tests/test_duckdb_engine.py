"""
Unit tests for DuckDB Financial Metric Engine module.
"""
import pytest
import json
from pathlib import Path
import pandas as pd
from src.engine.duckdb_engine import (
    FinancialMetricEngine, STANDARD_METRIC_MAP,
    US_GAAP_METRIC_MAP, INDIAN_METRIC_MAP, get_metric_map_for_market
)


@pytest.fixture
def temp_engine(tmp_path):
    db_file = tmp_path / "test_financials.duckdb"
    engine = FinancialMetricEngine(db_path=db_file)
    yield engine
    engine.close()


def test_engine_schema_initialization(temp_engine):
    df = temp_engine.conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_name = 'financial_facts'"
    ).df()
    assert not df.empty
    assert df["table_name"].iloc[0] == "financial_facts"


def test_ingest_and_query_facts_with_period_and_accession(temp_engine):
    sample_facts_data = {
        "ticker": "TEST",
        "facts": [
            {
                "concept": "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
                "label": "Revenue",
                "numeric_value": 1000000.0,
                "unit": "USD",
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "form": "10-K",
                "period_type": "duration",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31",
                "filed_date": "2025-01-30",
                "accession_number": "0000000000-25-000001"
            },
            {
                "concept": "us-gaap:NetIncomeLoss",
                "label": "Net Income",
                "numeric_value": 250000.0,
                "unit": "USD",
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "form": "10-K",
                "period_type": "duration",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31",
                "filed_date": "2025-01-30",
                "accession_number": "0000000000-25-000001"
            }
        ]
    }

    count = temp_engine.ingest_facts("TEST", sample_facts_data)
    assert count == 2

    # Test standard metric mapping query for "revenue"
    df_rev = temp_engine.query_metric("TEST", "revenue", year=2024)
    assert not df_rev.empty
    assert df_rev["val"].iloc[0] == 1000000.0
    assert df_rev["period_type"].iloc[0] == "duration"
    assert df_rev["accession_number"].iloc[0] == "0000000000-25-000001"

    # Test standard metric mapping query for "net_income"
    df_ni = temp_engine.query_metric("TEST", "net_income", year=2024)
    assert not df_ni.empty
    assert df_ni["val"].iloc[0] == 250000.0


def test_duplicate_prevention_and_delete_reinsert(temp_engine):
    sample_facts_data = {
        "ticker": "TEST",
        "facts": [
            {
                "concept": "us-gaap:Revenues",
                "numeric_value": 100.0,
                "fiscal_year": 2024,
                "fiscal_period": "FY"
            }
        ]
    }

    # Ingest twice
    temp_engine.ingest_facts("TEST", sample_facts_data)
    count = temp_engine.ingest_facts("TEST", sample_facts_data)
    assert count == 1

    df = temp_engine.query_metric("TEST", "Revenues")
    assert len(df) == 1


def test_get_available_concepts(temp_engine):
    sample_facts_data = {
        "ticker": "TEST",
        "facts": [
            {"concept": "us-gaap:Revenues", "label": "Revenues", "numeric_value": 100.0},
            {"concept": "us-gaap:Assets", "label": "Assets", "numeric_value": 500.0}
        ]
    }
    temp_engine.ingest_facts("TEST", sample_facts_data)

    concepts = temp_engine.get_available_concepts("TEST")
    assert "us-gaap:Revenues" in concepts
    assert "us-gaap:Assets" in concepts


def test_column_alignment_regression(temp_engine):
    sample_facts_data = {
        "ticker": "ALIGN_CHECK",
        "facts": [
            {
                "concept": "us-gaap:TestConcept",
                "label": "Test Label",
                "numeric_value": 999.0,
                "unit": "USD",
                "fiscal_year": 2024,
                "fiscal_period": "Q3",
                "form": "10-Q",
                "period_type": "DURATION_MARKER",
                "period_start": "2024-04-01",
                "period_end": "2024-06-30",
                "filed_date": "2024-07-25",
                "accession_number": "ACCESSION_MARKER_999"
            }
        ]
    }
    temp_engine.ingest_facts("ALIGN_CHECK", sample_facts_data)

    df_raw = temp_engine.conn.execute("SELECT * FROM financial_facts WHERE ticker = 'ALIGN_CHECK'").df()
    assert not df_raw.empty
    row = df_raw.iloc[0]

    assert row["ticker"] == "ALIGN_CHECK"
    assert row["form"] == "10-Q"
    assert row["fiscal_year"] == 2024
    assert row["fiscal_period"] == "Q3"
    assert row["concept"] == "us-gaap:TestConcept"
    assert row["label"] == "Test Label"
    assert row["val"] == 999.0
    assert row["unit"] == "USD"
    assert row["period_type"] == "DURATION_MARKER"
    assert row["period_start"] == "2024-04-01"
    assert row["period_end"] == "2024-06-30"
    assert row["filed_date"] == "2024-07-25"
    assert row["accession_number"] == "ACCESSION_MARKER_999"


def test_intra_batch_deduplication(temp_engine):
    sample_duplicate_batch = {
        "ticker": "INTRA_DEDUP",
        "facts": [
            {
                "concept": "us-gaap:Revenues",
                "label": "Revenues (Segment A)",
                "numeric_value": 100.0,
                "unit": "USD",
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31",
                "accession_number": "ACC-001"
            },
            {
                "concept": "us-gaap:Revenues",
                "label": "Revenues (Segment B)",
                "numeric_value": 100.0,
                "unit": "USD",
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "period_start": "2024-01-01",
                "period_end": "2024-12-31",
                "accession_number": "ACC-001"
            }
        ]
    }
    count = temp_engine.ingest_facts("INTRA_DEDUP", sample_duplicate_batch)
    assert count == 1


def test_real_aapl_xbrl_data(temp_engine):
    real_facts_file = Path("data/sec_corpus/AAPL/xbrl_facts.json")
    if real_facts_file.exists():
        with open(real_facts_file, "r", encoding="utf-8") as f:
            facts_data = json.load(f)

        count = temp_engine.ingest_facts("AAPL", facts_data)
        assert count > 1000

        # Query Revenue using standard metric map
        df = temp_engine.query_metric("AAPL", "revenue", year=2024, period="FY")
        assert not df.empty
        assert df["val"].iloc[0] > 1e11  # Apple revenue is ~$391 Billion


def test_detect_restatements(temp_engine):
    sample_facts_data = {
        "ticker": "RESTATE_TEST",
        "facts": [
            {
                "concept": "us-gaap:Revenues",
                "label": "Revenues",
                "numeric_value": 100000.0,
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "filed_date": "2025-01-15",
                "accession_number": "ACC-2024-ORIGINAL"
            },
            {
                "concept": "us-gaap:Revenues",
                "label": "Revenues",
                "numeric_value": 85000.0,
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "filed_date": "2025-06-20",
                "accession_number": "ACC-2024-AMENDED"
            }
        ]
    }
    temp_engine.ingest_facts("RESTATE_TEST", sample_facts_data)


    df_restated = temp_engine.detect_restatements("RESTATE_TEST", "revenue")
    assert not df_restated.empty
    assert len(df_restated) == 1
    assert df_restated["original_val"].iloc[0] == 100000.0
    assert df_restated["latest_val"].iloc[0] == 85000.0
    assert df_restated["variance_usd"].iloc[0] == -15000.0
    assert df_restated["variance_pct"].iloc[0] == -15.0


def test_schema_has_market_and_statement_type(temp_engine):
    cols = temp_engine.conn.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = 'financial_facts'"
    ).df()["column_name"].tolist()
    assert "market" in cols
    assert "statement_type" in cols


def test_get_metric_map_for_market():
    us_map = get_metric_map_for_market("US")
    assert "revenue" in us_map
    assert "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax" in us_map["revenue"]

    ind_map = get_metric_map_for_market("INDIA")
    assert "revenue" in ind_map
    assert "Total Revenue" in ind_map["revenue"]
    assert "Operating Revenue" in ind_map["revenue"]
    assert "gross_profit" in ind_map
    assert "total_debt" in ind_map


def test_indian_facts_ingestion_and_auto_detected_query(temp_engine):
    sample_indian_data = {
        "ticker": "RELIANCE.NS",
        "facts": [
            {
                "concept": "Total Revenue",
                "label": "Total Revenue",
                "numeric_value": 9000000000000.0,
                "unit": "INR",
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "form": "Annual Report",
                "market": "INDIA",
                "statement_type": "income_stmt",
                "period_type": "duration",
                "period_start": "2023-04-01",
                "period_end": "2024-03-31",
                "filed_date": "2024-05-15",
                "accession_number": "NSE-RELIANCE-2024"
            },
            {
                "concept": "Net Income",
                "label": "Net Income",
                "numeric_value": 690000000000.0,
                "unit": "INR",
                "fiscal_year": 2024,
                "fiscal_period": "FY",
                "form": "Annual Report",
                "market": "INDIA",
                "statement_type": "income_stmt",
                "period_type": "duration",
                "period_start": "2023-04-01",
                "period_end": "2024-03-31",
                "filed_date": "2024-05-15",
                "accession_number": "NSE-RELIANCE-2024"
            }
        ]
    }

    count = temp_engine.ingest_facts("RELIANCE.NS", sample_indian_data)
    assert count == 2

    # Query with auto-detection of INDIA from .NS suffix
    df_rev = temp_engine.query_metric("RELIANCE.NS", "revenue", year=2024)
    assert not df_rev.empty
    assert df_rev["val"].iloc[0] == 9000000000000.0
    assert df_rev["market"].iloc[0] == "INDIA"
    assert df_rev["statement_type"].iloc[0] == "income_stmt"

    # Query with explicit market="INDIA"
    df_ni = temp_engine.query_metric("RELIANCE.NS", "net_income", year=2024, market="INDIA")
    assert not df_ni.empty
    assert df_ni["val"].iloc[0] == 690000000000.0


