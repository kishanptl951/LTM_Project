"""
Naive RAG vs. DuckDB Precision Engine Benchmark Suite:
Compares Naive Vector RAG (fixed-size chunk text search) vs. DuckDB SQL Engine
against 7 verified ground truth financial queries from SEC EDGAR 10-K filings.
"""
import re
import json
import pytest
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.engine.duckdb_engine import FinancialMetricEngine
from src.engine.duckdb_engine import FinancialMetricEngine
import uuid
import chromadb


# Verified Ground Truth Financial Facts from SEC EDGAR Filings
GROUND_TRUTH_QUERIES: List[Dict[str, Any]] = [
    {
        "query": "What was AAPL FY 2024 Revenue?",
        "ticker": "AAPL",
        "concept": "revenue",
        "fiscal_year": 2024,
        "fiscal_period": "FY",
        "ground_truth_val": 391035000000.0,
        "ground_truth_str": "$391,035,000,000",
    },
    {
        "query": "What was AAPL FY 2023 Revenue?",
        "ticker": "AAPL",
        "concept": "revenue",
        "fiscal_year": 2023,
        "fiscal_period": "FY",
        "ground_truth_val": 383285000000.0,
        "ground_truth_str": "$383,285,000,000",
    },
    {
        "query": "What was AAPL FY 2024 Net Income?",
        "ticker": "AAPL",
        "concept": "net_income",
        "fiscal_year": 2024,
        "fiscal_period": "FY",
        "ground_truth_val": 93736000000.0,
        "ground_truth_str": "$93,736,000,000",
    },
    {
        "query": "What was AAPL FY 2024 Total Assets?",
        "ticker": "AAPL",
        "concept": "total_assets",
        "fiscal_year": 2024,
        "fiscal_period": "FY",
        "ground_truth_val": 364980000000.0,
        "ground_truth_str": "$364,980,000,000",
    },
    {
        "query": "What was AAPL FY 2024 Operating Income?",
        "ticker": "AAPL",
        "concept": "operating_income",
        "fiscal_year": 2024,
        "fiscal_period": "FY",
        "ground_truth_val": 123216000000.0,
        "ground_truth_str": "$123,216,000,000",
    },
    {
        "query": "What was TSLA FY 2025 Total Assets?",
        "ticker": "TSLA",
        "concept": "total_assets",
        "fiscal_year": 2025,
        "fiscal_period": "FY",
        "ground_truth_val": 137806000000.0,
        "ground_truth_str": "$137,806,000,000",
    },
    {
        "query": "What was TSLA FY 2025 Net Income?",
        "ticker": "TSLA",
        "concept": "net_income",
        "fiscal_year": 2025,
        "fiscal_period": "FY",
        "ground_truth_val": 3794000000.0,
        "ground_truth_str": "$3,794,000,000",
    },

]


def _extract_number_from_text(text: str) -> Optional[float]:
    """Helper for Naive RAG text extraction heuristic."""
    # Find all dollar amounts or large numbers in text
    matches = re.findall(r"\$\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(billion|million)?", text, re.IGNORECASE)
    if not matches:
        # Fallback to plain large numbers
        raw_nums = re.findall(r"\b\d{1,3}(?:,\d{3})+\b", text)
        if raw_nums:
            try:
                return float(raw_nums[0].replace(",", ""))
            except ValueError:
                return None
        return None

    first_match = matches[0]
    num_str = first_match[0].replace(",", "")
    multiplier_str = first_match[1].lower() if len(first_match) > 1 else ""

    try:
        val = float(num_str)
        if "billion" in multiplier_str:
            val *= 1e9
        elif "million" in multiplier_str:
            val *= 1e6
        return val
    except ValueError:
        return None


def test_naive_vs_duckdb_precision_comparison():
    """
    Executes comparison test between Naive Vector RAG and DuckDB SQL Engine.
    Validates that DuckDB achieves 100% precision while Naive RAG exhibits errors/hallucinations on tables.
    """
    db_engine = FinancialMetricEngine()
    naive_clients = {}
    def get_naive_text(query: str, ticker: str) -> str:
        if ticker not in naive_clients:
            parsed_file = Path(f"data/sec_corpus/{ticker}/parsed_sections.json")
            if not parsed_file.exists():
                naive_clients[ticker] = None
                return ""
            
            with open(parsed_file, "r", encoding="utf-8") as f:
                sections = json.load(f)
            
            full_text = "".join(sections.values())
            
            chunk_size = 1000
            chunk_overlap = 100
            chunks = []
            
            start = 0
            while start < len(full_text):
                end = start + chunk_size
                chunks.append(full_text[start:end])
                start += (chunk_size - chunk_overlap)
                
            client = chromadb.Client()
            collection = client.create_collection(name=f"naive_{ticker}_{uuid.uuid4().hex}")
            
            batch_size = 500
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                collection.add(
                    documents=batch,
                    ids=[str(j) for j in range(i, i+len(batch))]
                )
            naive_clients[ticker] = collection

        collection = naive_clients[ticker]
        if not collection: return ""
        
        results = collection.query(query_texts=[query], n_results=1)
        if results and results["documents"] and results["documents"][0]:
            return results["documents"][0][0]
        return ""

    comparison_results: List[Dict[str, Any]] = []
    duckdb_correct = 0
    naive_correct = 0

    for item in GROUND_TRUTH_QUERIES:
        q = item["query"]
        gt_val = item["ground_truth_val"]
        ticker = item["ticker"]
        concept = item["concept"]
        year = item["fiscal_year"]

        # 1. DuckDB Precision Execution
        df_duckdb = db_engine.query_metric(ticker=ticker, concept=concept, year=year)
        duckdb_val = float(df_duckdb["val"].iloc[0]) if not df_duckdb.empty else None
        duckdb_is_correct = bool(duckdb_val is not None and abs(duckdb_val - gt_val) < 1.0)
        if duckdb_is_correct:
            duckdb_correct += 1

        # 2. True Naive Vector RAG Execution (Fixed-size chunking over raw text, purely dense vector retrieval)
        naive_text = get_naive_text(q, ticker)
        naive_val = _extract_number_from_text(naive_text)
        naive_is_correct = bool(naive_val is not None and abs(naive_val - gt_val) < 1e6)
        if naive_is_correct:
            naive_correct += 1

        comparison_results.append({
            "query": q,
            "ticker": ticker,
            "ground_truth": item["ground_truth_str"],
            "ground_truth_val": gt_val,
            "duckdb": {
                "extracted_val": duckdb_val,
                "is_correct": duckdb_is_correct,
                "error": None if duckdb_is_correct else "Value mismatch",
            },
            "naive_rag": {
                "extracted_val": naive_val,
                "passage_snippet": naive_text[:120] + "..." if naive_text else "No passage found",
                "is_correct": naive_is_correct,
                "error": None if naive_is_correct else "Table chunk fragmentation / loss of column context",
            }
        })

    duckdb_accuracy = duckdb_correct / len(GROUND_TRUTH_QUERIES)
    naive_accuracy = naive_correct / len(GROUND_TRUTH_QUERIES)

    summary = {
        "total_queries_tested": len(GROUND_TRUTH_QUERIES),
        "duckdb_accuracy": f"{duckdb_accuracy:.1%}",
        "naive_rag_accuracy": f"{naive_accuracy:.1%}",
        "accuracy_delta": f"{(duckdb_accuracy - naive_accuracy):.1%}",
        "comparison_table": comparison_results
    }

    # Save summary artifact
    out_file = Path("data/sec_corpus/naive_vs_duckdb_comparison.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    assert out_file.exists()
    assert duckdb_accuracy == 1.0, f"DuckDB precision fell below 100%: got {duckdb_accuracy:.1%}"
