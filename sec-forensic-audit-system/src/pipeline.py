"""
End-to-End Orchestrator Pipeline for Dual-Market Forensic Audit System (US + India).
Runs Ingestion -> DB Storage -> Retrieval Indexing -> Query Routing -> Contradiction Verification.
Auto-detects market (US/India) from ticker and routes to the appropriate data source.
"""
import sys
import logging

# Fix: truststore v0.10.4 on Python 3.11 causes SSLContext.verify_mode recursion (~500 deep).
# Increasing the limit prevents RecursionError during SEC EDGAR HTTPS handshakes.
sys.setrecursionlimit(10000)
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import Optional

from src.config import DEFAULT_TICKER, DEFAULT_FORM_TYPE, DEFAULT_INDIAN_TICKER, MARKET_US, MARKET_INDIA
from src.ingestion.market_router import detect_market, normalize_ticker, format_value
from src.engine.duckdb_engine import FinancialMetricEngine
from src.retrieval.chunker import SectionChunker
from src.retrieval.hybrid_search import HybridSearchEngine
from src.router.query_router import DeterministicRouter, QueryType
from src.router.verifier import ContradictionVerifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Pipeline")


def run_pipeline(ticker: str = DEFAULT_TICKER, form_type: str = DEFAULT_FORM_TYPE, year: Optional[int] = None, market: Optional[str] = None):
    """
    Executes full end-to-end ingestion and processing pipeline for a given ticker.
    Auto-detects market (US/India) from ticker if not explicitly provided.
    """
    # Auto-detect market
    if market is None:
        market = detect_market(ticker)
    ticker = normalize_ticker(ticker, market)

    currency_sym = "$" if market == MARKET_US else "₹"
    logger.info(f"=== Starting Forensic Audit Pipeline for Ticker: {ticker} (Market: {market}) ===")

    # ---------------------------------------------------------------------------
    # 1. Track A & B Ingestion (market-specific)
    # ---------------------------------------------------------------------------
    if market == MARKET_INDIA:
        logger.info("Step 1: Ingesting financial data from Yahoo Finance (Indian Market)...")
        from src.ingestion.nse_fetcher import NSEFetcher
        fetcher = NSEFetcher()
        facts_data = fetcher.fetch_company_facts(ticker)
        html_content = ""  # No HTML filing for Indian market via yfinance
        logger.info(f"Ingestion complete for {ticker}. Loaded {len(facts_data.get('facts', []))} financial facts.")
    else:
        logger.info("Step 1: Ingesting SEC EDGAR XBRL facts and HTML filing (US Market)...")
        from src.ingestion.edgar_fetcher import EdgarFetcher
        fetcher = EdgarFetcher()
        facts_data = fetcher.fetch_company_facts(ticker)
        html_content = fetcher.fetch_filing_html(ticker, form_type=form_type, year=year)
        logger.info(f"Ingestion complete for {ticker}. Loaded {len(facts_data.get('facts', []))} XBRL facts and {len(html_content)} bytes of HTML.")

    # ---------------------------------------------------------------------------
    # 2. Parse regulatory sections (market-specific)
    # ---------------------------------------------------------------------------
    sections = {}
    if market == MARKET_INDIA:
        # Indian annual report parsing (if HTML/text available)
        if html_content:
            logger.info("Step 2: Parsing Indian annual report sections (MD&A, Board Report, Notes, Auditor Report)...")
            from src.ingestion.indian_report_parser import IndianReportParser
            parser = IndianReportParser()
            sections = parser.extract_sections(html_content)
        else:
            logger.info("Step 2: Skipping section parsing (no annual report text available for Indian market via yfinance).")
            sections = {"mda": "", "board_report": "", "notes": "", "auditor_report": ""}
    else:
        logger.info("Step 2: Parsing regulatory sections (Item 1A, Item 7, Item 8)...")
        from src.ingestion.sec_parser import SECParser
        parser = SECParser()
        sections = parser.extract_sections(html_content)

    logger.info(f"Section parsing complete: {', '.join(f'{k} ({len(v)} chars)' for k, v in sections.items())}")

    # Save parsed sections to output disk file
    output_dir = Path(f"data/{'nse_corpus' if market == MARKET_INDIA else 'sec_corpus'}/{ticker.replace('.NS', '').replace('.BO', '')}")
    output_dir.mkdir(parents=True, exist_ok=True)
    sections_file = output_dir / "parsed_sections.json"
    import json
    with open(sections_file, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2)
    logger.info(f"Saved parsed sections to {sections_file}")

    # ---------------------------------------------------------------------------
    # 3. DuckDB Financial Fact Storage & Query Testing
    # ---------------------------------------------------------------------------
    logger.info("Step 3: Storing financial facts into DuckDB database...")
    db_engine = FinancialMetricEngine()
    inserted_count = db_engine.ingest_facts(ticker, facts_data)
    logger.info(f"DuckDB ingestion complete: stored {inserted_count} numeric facts for {ticker}.")

    # Run sample test query
    sample_df = db_engine.query_metric(ticker, "Revenue", year=year, market=market)
    if not sample_df.empty:
        logger.info(f"Sample DuckDB Query Result for {ticker} Revenue:\n{sample_df.head(3).to_string()}")

    # ---------------------------------------------------------------------------
    # 4. Qualitative Section-Aware Chunking & Hybrid Retrieval Indexing
    # ---------------------------------------------------------------------------
    has_sections = any(len(v) > 0 for v in sections.values())
    if has_sections:
        logger.info("Step 4: Chunking sections and building ChromaDB + BM25 Hybrid Index...")
        chunker = SectionChunker(chunk_size=1200, overlap=200)
        chunks = chunker.chunk_all_sections(sections, ticker=ticker, fiscal_year=year)

        hybrid_engine = HybridSearchEngine()
        indexed_chunks_count = hybrid_engine.index_chunks(chunks)
        logger.info(f"Hybrid Search Engine ready: indexed {indexed_chunks_count} section passages.")

        # Run sample hybrid search query
        sample_search_query = "supply chain disruptions and inventory risk" if market == MARKET_US else "related party transactions and promoter pledging"
        search_results = hybrid_engine.search(sample_search_query, top_k=3, ticker_filter=ticker)
        if search_results:
            logger.info(f"Sample Hybrid Search Reranked Result for '{sample_search_query}':")
            for idx, res in enumerate(search_results, 1):
                logger.info(f"  [{idx}] Citation: {res.get('citation')} | Score: {res.get('score'):.4f}")
                logger.info(f"      Text: {res.get('text', '')[:180]}...")
    else:
        logger.info("Step 4: Skipping hybrid indexing (no section text available).")
        hybrid_engine = HybridSearchEngine()
        search_results = []
        indexed_chunks_count = 0

    # ---------------------------------------------------------------------------
    # 5. Phase 4: Deterministic Query Router & Contradiction Verification
    # ---------------------------------------------------------------------------
    logger.info("Step 5: Phase 4 — Deterministic Query Router & Contradiction Verifier...")
    router = DeterministicRouter()
    verifier = ContradictionVerifier(hybrid_engine=hybrid_engine)

    # Test queries based on market
    if market == MARKET_INDIA:
        base_ticker = ticker.replace(".NS", "").replace(".BO", "")
        test_queries = [
            f"Did {base_ticker} restate 2023 revenue figures?",
            f"What was {ticker} FY 2024 Revenue?",
            f"What are the key risks for {base_ticker}?",
            f"Check if {base_ticker} MD&A claims contradict Notes to Accounts",
        ]
    else:
        test_queries = [
            f"Did {ticker} restate 2023 revenue figures?",
            f"What was {ticker} Q2 2024 Revenue?",
            f"What are the key supply chain risks for {ticker}?",
            f"Check if {ticker} Item 7 revenue claims contradict Item 8 footnotes",
        ]

    route_results = []
    for tq in test_queries:
        route = router.route_query(tq)
        route_type = route["route_type"]
        logger.info(
            f"  Query: '{tq}' => Route: {route_type.value} | "
            f"Ticker: {route.get('ticker')} | Concept: {route.get('concept')} | "
            f"Year: {route.get('fiscal_year')} | Period: {route.get('fiscal_period')} | "
            f"Market: {route.get('market')}"
        )

        # Execute the routed action
        if route_type == QueryType.NUMERIC:
            concept = route.get("concept") or "Revenue"
            result_df = db_engine.query_metric(
                ticker=route.get("ticker") or ticker,
                concept=concept,
                year=route.get("fiscal_year"),
                period=route.get("fiscal_period"),
                market=market,
            )
            logger.info(f"    DuckDB Result: {len(result_df)} rows returned.")
            if not result_df.empty:
                for _, row in result_df.head(3).iterrows():
                    logger.info(f"      {row['fiscal_year']} {row['fiscal_period']}: {format_value(row['val'], market)}")

        elif route_type == QueryType.NARRATIVE:
            narrative_results = hybrid_engine.search(
                query=tq, top_k=3,
                ticker_filter=route.get("ticker") or ticker,
                section_filter=route.get("section_filter"),
            )
            logger.info(f"    Hybrid Search: {len(narrative_results)} passages returned.")
            for idx, nr in enumerate(narrative_results[:2], 1):
                logger.info(f"      [{idx}] {nr.get('citation')} | Score: {nr.get('score', 0):.4f}")

        elif route_type == QueryType.CONTRADICTION:
            verification = verifier.verify(
                query=tq,
                ticker=route.get("ticker") or ticker,
                top_k=3,
                market=market,
            )
            logger.info(f"    Contradiction Result: severity={verification['severity']}, has_contradiction={verification['has_contradiction']}")
            logger.info(f"    Risk Signals: {verification.get('risk_signals_found', [])}")
            logger.info(f"    Analysis: {verification.get('analysis', '')[:300]}")

        elif route_type == QueryType.RESTATEMENT:
            concept = route.get("concept") or "revenue"
            restatement_df = db_engine.detect_restatements(
                ticker=route.get("ticker") or ticker,
                concept=concept,
                year=route.get("fiscal_year")
            )
            logger.info(f"    Restatement Result: {len(restatement_df)} restatement variance records found.")
            if not restatement_df.empty:
                for _, row in restatement_df.head(3).iterrows():
                    logger.info(
                        f"      {row['fiscal_year']} {row['concept']}: "
                        f"Original {format_value(row['original_val'], market)} -> "
                        f"Latest {format_value(row['latest_val'], market)} "
                        f"(Var: {row['variance_pct']:.2f}%)"
                    )

        route_results.append({
            "query": tq,
            "route_type": route_type.value,
            "ticker": route.get("ticker"),
            "concept": route.get("concept"),
            "fiscal_year": route.get("fiscal_year"),
            "fiscal_period": route.get("fiscal_period"),
            "market": market,
        })

    # Run a full contradiction verification pass
    if has_sections:
        logger.info(f"Step 5b: Full contradiction verification for {ticker}...")
        if market == MARKET_INDIA:
            contradiction_query = f"{ticker} revenue growth and related party transactions"
        else:
            contradiction_query = f"{ticker} revenue growth outlook and inventory valuation"
        full_verification = verifier.verify(query=contradiction_query, ticker=ticker, top_k=3, market=market)
        logger.info(f"  Full Verification: severity={full_verification['severity']}")
        logger.info(f"  Analysis: {full_verification.get('analysis', '')[:400]}")
    else:
        full_verification = {"has_contradiction": False, "severity": "none", "analysis": "No sections available for contradiction verification.", "risk_signals_found": [], "citations": []}

    summary_file = output_dir / "pipeline_summary.json"
    summary_data = {
        "ticker": ticker,
        "market": market,
        "xbrl_facts_count": len(facts_data.get("facts", [])),
        "duckdb_facts_stored": inserted_count,
        "parsed_sections": {k: len(v) for k, v in sections.items()},
        "hybrid_chunks_indexed": indexed_chunks_count,
        "sample_revenue_query": sample_df.head(5).to_dict(orient="records") if not sample_df.empty else [],
        "sample_hybrid_search_results": search_results,
        "phase4_route_results": route_results,
        "phase4_contradiction_verification": {
            "query": full_verification.get("query", ""),
            "has_contradiction": full_verification["has_contradiction"],
            "severity": full_verification["severity"],
            "analysis": full_verification.get("analysis", ""),
            "risk_signals_found": full_verification.get("risk_signals_found", []),
            "citations": full_verification.get("citations", []),
        },
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, default=str)
    logger.info(f"Saved pipeline execution summary to {summary_file}")

    logger.info(f"=== Pipeline Completed Successfully for {ticker} (Market: {market}) ===")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Dual-Market Forensic Audit Pipeline (US + India)")
    parser.add_argument("--ticker", type=str, default=DEFAULT_TICKER, help="Company ticker (e.g. AAPL, RELIANCE.NS)")
    parser.add_argument("--form", type=str, default=DEFAULT_FORM_TYPE, help="Filing form type (US: 10-K/10-Q)")
    parser.add_argument("--year", type=int, default=None, help="Filing year (optional)")
    parser.add_argument("--market", type=str, default=None, choices=["US", "INDIA"], help="Force market (auto-detected if omitted)")

    args = parser.parse_args()
    run_pipeline(ticker=args.ticker, form_type=args.form, year=args.year, market=args.market)
