"""
Streamlit SEC EDGAR Forensic Audit System Dashboard.
Provides a premium financial interface with glassmorphism CSS styling:
- Sidebar: Company Ticker, Fiscal Filters, Query Execution Mode, Quick Presets
- Main Panel 1 (Middle): Audit Findings, DuckDB Metrics, Restatement Alerts & Contradiction Reasoning
- Main Panel 2 (Right): Source Citations, XBRL Tag Provenance & SEC EDGAR Document Inspector
"""
import sys

# Fix: truststore v0.10.4 on Python 3.11 causes SSLContext.verify_mode recursion (~500 deep).
# Increasing the limit prevents RecursionError during SEC EDGAR HTTPS handshakes.
sys.setrecursionlimit(10000)

import logging
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Apply SSL fix for truststore on Windows Python 3.11
import src.ssl_fix  # noqa: F401

import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from typing import Dict, Any, List, Optional

from src.config import (
    DEFAULT_TICKER, DATA_DIR, LLM_VERIFIER_ENABLED,
    MARKET_US, MARKET_INDIA, DEFAULT_INDIAN_TICKER,
    INDIAN_DATA_DIR,
)
from src.engine.duckdb_engine import FinancialMetricEngine
from src.retrieval.hybrid_search import HybridSearchEngine
from src.router.query_router import DeterministicRouter, QueryType
from src.router.verifier import ContradictionVerifier
from src.ingestion.market_router import (
    detect_market, normalize_ticker, format_value as format_currency,
    KNOWN_INDIAN_TICKERS, KNOWN_US_TICKERS
)
from src.ingestion.nse_fetcher import NSEFetcher

# Configure Page Layout & Title
st.set_page_config(
    page_title="Dual-Market Forensic Audit Engine (US & India)",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium CSS Injection for Glassmorphism & High-Contrast Financial Aesthetics
st.markdown("""
<style>
    /* Dark Slate & Emerald Glassmorphism Canvas */
    .stApp {
        background-color: #090d16;
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* High-contrast Black Text Input & Text Area Styling */
    .stTextArea textarea, div[data-baseweb="textarea"] textarea, .stTextInput input, div[data-baseweb="input"] input {
        color: #ffffff !important;
        background-color: #000000 !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        border: 2px solid #0284c7 !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15) !important;
    }
    
    /* Dark Slate High-Contrast Placeholder */
    .stTextArea textarea::placeholder, div[data-baseweb="textarea"] textarea::placeholder, .stTextInput input::placeholder {
        color: #64748b !important;
        font-weight: 600 !important;
        opacity: 0.95 !important;
    }
    
    /* Active Focus State */
    .stTextArea textarea:focus, div[data-baseweb="textarea"] textarea:focus, .stTextInput input:focus {
        border-color: #10b981 !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.4) !important;
    }
    
    /* Glass Header Banner */
    .main-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 50%, rgba(6, 78, 59, 0.8) 100%);
        backdrop-filter: blur(12px);
        padding: 22px 28px;
        border-radius: 14px;
        border: 1px solid rgba(16, 185, 129, 0.25);
        margin-bottom: 18px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    .main-header h1 {
        color: #34d399;
        font-size: 2.1rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #94a3b8;
        margin: 6px 0 0 0;
        font-size: 0.92rem;
    }

    /* KPI Summary Stat Pill */
    .stat-pill {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(51, 65, 85, 0.8);
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 0.82rem;
        color: #cbd5e1;
        display: inline-block;
        margin-right: 8px;
    }
    .stat-pill strong {
        color: #34d399;
    }
    
    /* Panel Cards */
    .panel-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(51, 65, 85, 0.7);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 18px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    
    /* Glowing Route Badges */
    .badge-numeric {
        background-color: rgba(6, 95, 70, 0.7);
        color: #6ee7b7;
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.83rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #10b981;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }
    .badge-narrative {
        background-color: rgba(30, 58, 138, 0.7);
        color: #93c5fd;
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.83rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #3b82f6;
        box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
    }
    .badge-contradiction {
        background-color: rgba(131, 24, 67, 0.7);
        color: #fbcfe8;
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.83rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #ec4899;
        box-shadow: 0 0 10px rgba(236, 72, 153, 0.3);
    }
    .badge-restatement {
        background-color: rgba(146, 64, 14, 0.7);
        color: #fde68a;
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.83rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #f59e0b;
        box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
    }
    .badge-full-audit {
        background: linear-gradient(90deg, rgba(6, 95, 70, 0.7), rgba(30, 58, 138, 0.7));
        color: #a5f3fc;
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.83rem;
        font-weight: 700;
        display: inline-block;
        border: 1px solid #06b6d4;
        box-shadow: 0 0 10px rgba(6, 182, 212, 0.3);
    }
    
    /* Contradiction Alert Banners */
    .alert-none {
        background: linear-gradient(90deg, rgba(6, 78, 59, 0.8) 0%, rgba(2, 44, 34, 0.8) 100%);
        border-left: 5px solid #10b981;
        padding: 14px;
        border-radius: 8px;
        margin-top: 12px;
    }
    .alert-qualification {
        background: linear-gradient(90deg, rgba(120, 53, 15, 0.8) 0%, rgba(69, 26, 3, 0.8) 100%);
        border-left: 5px solid #f59e0b;
        padding: 14px;
        border-radius: 8px;
        margin-top: 12px;
    }
    .alert-contradiction {
        background: linear-gradient(90deg, rgba(131, 24, 67, 0.8) 0%, rgba(80, 7, 36, 0.8) 100%);
        border-left: 5px solid #ef4444;
        padding: 14px;
        border-radius: 8px;
        margin-top: 12px;
    }
    
    /* Risk Tags */
    .risk-tag {
        background-color: rgba(127, 29, 29, 0.8);
        color: #fca5a5;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.80rem;
        font-weight: 700;
        margin-right: 6px;
        margin-top: 4px;
        display: inline-block;
        border: 1px solid #ef4444;
    }

    /* EDGAR Link Button */
    .edgar-link-btn {
        background-color: #1e293b;
        color: #38bdf8 !important;
        border: 1px solid #0284c7;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none;
        display: inline-block;
        margin-top: 8px;
    }
    .edgar-link-btn:hover {
        background-color: #0284c7;
        color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Human-Readable Number Formatting Utility
# ---------------------------------------------------------------------------
def format_value(val: Any, prefix: str = "$", decimals: int = 1, market: str = "US") -> str:
    """
    Converts raw numeric values into human-readable short form.
    US: 2000000000 -> $2.0B, 150300000 -> $150.3M
    INDIA: 2000000000 -> ₹200.00 Cr, 150300000 -> ₹15.03 Cr
    """
    if val is None:
        return "N/A"
    try:
        num = float(val)
    except (ValueError, TypeError):
        return str(val)

    if market == MARKET_INDIA or market == "INDIA":
        return format_currency(num, market=MARKET_INDIA)

    negative = num < 0
    abs_num = abs(num)
    sign = "-" if negative else ""

    if abs_num >= 1_000_000_000_000:
        formatted = f"{sign}{prefix}{abs_num / 1_000_000_000_000:.{decimals}f}T"
    elif abs_num >= 1_000_000_000:
        formatted = f"{sign}{prefix}{abs_num / 1_000_000_000:.{decimals}f}B"
    elif abs_num >= 1_000_000:
        formatted = f"{sign}{prefix}{abs_num / 1_000_000:.{decimals}f}M"
    elif abs_num >= 1_000:
        formatted = f"{sign}{prefix}{abs_num / 1_000:.{decimals}f}K"
    else:
        formatted = f"{sign}{prefix}{abs_num:,.{decimals}f}"

    return formatted


def _plotly_dark_layout(fig: go.Figure, title: str = "", y_title: str = "", x_title: str = "") -> go.Figure:
    """Applies a consistent premium dark theme to Plotly figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(color="#e2e8f0", size=16), x=0.02),
        paper_bgcolor="rgba(15, 23, 42, 0.9)",
        plot_bgcolor="rgba(15, 23, 42, 0.5)",
        font=dict(color="#cbd5e1", family="Inter, system-ui, sans-serif"),
        xaxis=dict(
            title=x_title,
            gridcolor="rgba(51, 65, 85, 0.5)",
            linecolor="rgba(51, 65, 85, 0.8)",
            tickfont=dict(color="#94a3b8"),
        ),
        yaxis=dict(
            title=y_title,
            gridcolor="rgba(51, 65, 85, 0.5)",
            linecolor="rgba(51, 65, 85, 0.8)",
            tickfont=dict(color="#94a3b8"),
        ),
        margin=dict(l=60, r=30, t=50, b=50),
        legend=dict(font=dict(color="#94a3b8")),
        hoverlabel=dict(bgcolor="#1e293b", font_size=13, font_color="#e2e8f0"),
    )
    return fig


# ---------------------------------------------------------------------------
# Cached Engine Singletons
# ---------------------------------------------------------------------------
@st.cache_resource
def get_db_engine():
    return FinancialMetricEngine()

@st.cache_resource
def get_hybrid_engine():
    return HybridSearchEngine()

@st.cache_resource
def get_router():
    return DeterministicRouter()

@st.cache_resource
def get_verifier():
    hybrid_engine = get_hybrid_engine()
    return ContradictionVerifier(hybrid_engine=hybrid_engine)


db_engine = get_db_engine()
hybrid_engine = get_hybrid_engine()
router = get_router()
verifier = get_verifier()


# Helper function for auto-ingesting ticker data if not yet present in DuckDB/ChromaDB
def _ensure_ticker_ingested(ticker: str, db_engine: FinancialMetricEngine, hybrid_engine: HybridSearchEngine, market: Optional[str] = None):
    """
    Ensures facts and regulatory section chunks exist in DuckDB and ChromaDB for the ticker.
    Supports both US (SEC EDGAR) and Indian (NSE/yfinance) markets.
    """
    if not market:
        market = detect_market(ticker)
    ticker = normalize_ticker(ticker, market)

    if market == MARKET_INDIA:
        df_check = db_engine.query_metric(ticker=ticker, concept="revenue", market=MARKET_INDIA)
        if df_check.empty:
            try:
                fetcher = NSEFetcher()
                success = fetcher.ingest_to_duckdb(ticker, db_engine)
                if not success:
                    st.warning(f"Could not fetch financial statements for Indian ticker {ticker} via yfinance.")
            except Exception as e:
                st.error(f"Failed to ingest Indian market data for {ticker}: {e}")

        # Index Indian narrative sections into ChromaDB for Narrative & Contradiction routes
        from src.ingestion.indian_report_parser import IndianReportParser
        from src.retrieval.chunker import SectionChunker

        base_ticker = ticker.replace(".NS", "").replace(".BO", "").upper()
        ticker_dir = INDIAN_DATA_DIR / base_ticker if INDIAN_DATA_DIR.exists() else Path(f"data/nse_corpus/{base_ticker}")
        sections_file = ticker_dir / "parsed_sections.json"

        sections = {}
        if sections_file.exists():
            try:
                with open(sections_file, "r", encoding="utf-8") as f:
                    sections = json.load(f)
            except Exception:
                sections = {}

        if not sections:
            # No pre-parsed sections available; Indian reports via yfinance don't include HTML text
            # If a user has manually placed an annual report HTML/text, parse it
            report_file = ticker_dir / "annual_report.html"
            if report_file.exists():
                try:
                    with open(report_file, "r", encoding="utf-8") as f:
                        report_html = f.read()
                    parser = IndianReportParser()
                    sections = parser.extract_sections(report_html)
                    ticker_dir.mkdir(parents=True, exist_ok=True)
                    with open(sections_file, "w", encoding="utf-8") as f:
                        json.dump(sections, f, indent=2)
                except Exception as ex:
                    logging.warning(f"Could not parse Indian annual report for {ticker}: {ex}")

        if sections and any(len(v) > 0 for v in sections.values()):
            chunker = SectionChunker()
            chunks = chunker.chunk_all_sections(sections, ticker=ticker)
            if chunks:
                hybrid_engine.index_chunks(chunks)
    else:
        from src.ingestion.edgar_fetcher import EdgarFetcher
        from src.ingestion.sec_parser import SECParser
        from src.retrieval.chunker import SectionChunker

        ticker = ticker.upper()
        df_check = db_engine.query_metric(ticker=ticker, concept="revenue", market=MARKET_US)
        if df_check.empty:
            try:
                fetcher = EdgarFetcher()
                facts_data = fetcher.fetch_company_facts(ticker)
                if facts_data.get("facts"):
                    db_engine.ingest_facts(ticker, facts_data)
                    
                ticker_dir = DATA_DIR / ticker
                sections_file = ticker_dir / "parsed_sections.json"
                if not sections_file.exists():
                    try:
                        html_content = fetcher.fetch_filing_html(ticker, form_type="10-K")
                        parser = SECParser()
                        sections = parser.extract_sections(html_content)
                        with open(sections_file, "w", encoding="utf-8") as f:
                            json.dump(sections, f, indent=2)
                    except Exception as ex:
                        logging.warning(f"Could not fetch/parse HTML sections for {ticker}: {ex}")
                        sections = {}
                else:
                    with open(sections_file, "r", encoding="utf-8") as f:
                        sections = json.load(f)
                        
                if sections:
                    chunker = SectionChunker()
                    chunks = chunker.chunk_all_sections(sections, ticker=ticker)
                    if chunks:
                        hybrid_engine.index_chunks(chunks)
            except Exception as e:
                st.error(f"Failed to ingest SEC EDGAR data for {ticker}: {e}")


# Initialize session states
if "user_query_input" not in st.session_state:
    st.session_state.user_query_input = "What was AAPL Q2 2026 Revenue?"

if "audit_results" not in st.session_state:
    st.session_state.audit_results = None


# ---------------------------------------------------------------------------
# Header Banner
# ---------------------------------------------------------------------------
verifier_badge = "🟢 <strong>Gemini Flash Active (gemini-flash-latest)</strong>" if LLM_VERIFIER_ENABLED else "🟡 <strong>Rule-based Heuristic Mode</strong>"

st.markdown(f"""
<div class="main-header">
    <h1>🕵️‍♂️ Dual-Market Forensic Audit Engine</h1>
    <p>Zero-Hallucination DuckDB SQL Engine (US-GAAP & Ind-AS) + Section-Aware Hybrid Retrieval + Dual-Pass Verifier</p>
    <div style="margin-top: 12px;">
        <span class="stat-pill">🌐 Markets: <strong>🇺🇸 US (SEC) & 🇮🇳 India (NSE/BSE)</strong></span>
        <span class="stat-pill">⚡ Engine: <strong>DuckDB SQL</strong></span>
        <span class="stat-pill">🔍 Search: <strong>ChromaDB + BM25 + Flashrank</strong></span>
        <span class="stat-pill">⚖️ Verifier: {verifier_badge}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# SIDEBAR CONTROL PANEL
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## ⚙️ Control Panel")
    
    # Financial Market Selector
    selected_market_label = st.radio(
        "🌐 Select Financial Market",
        ["🇺🇸 US Market (SEC / US-GAAP)", "🇮🇳 Indian Market (NSE / Ind-AS)"],
        index=0,
        help="Switch between US SEC EDGAR and Indian NSE/BSE markets"
    )
    is_india = "Indian" in selected_market_label
    current_market = MARKET_INDIA if is_india else MARKET_US
    
    # Target Company Ticker
    if is_india:
        ticker_choices = [
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS",
            "ICICIBANK.NS", "TATAMOTORS.NS", "WIPRO.NS", "SBIN.NS",
            "ITC.NS", "BHARTIARTL.NS", "Custom..."
        ]
        default_idx = 0
    else:
        ticker_choices = [
            "AAPL", "TSLA", "RMD", "JPM", "NVDA", "MSFT", "GOOGL", "AMZN", "Custom..."
        ]
        default_idx = 0

    selected_choice = st.selectbox(
        "Target Company Ticker",
        ticker_choices,
        index=default_idx,
        help="Select or enter target company ticker"
    )
    if selected_choice == "Custom...":
        custom_ticker = st.text_input("Enter Custom Ticker", value="TATAMOTORS.NS" if is_india else "META")
        selected_ticker = custom_ticker.strip().upper()
    else:
        selected_ticker = selected_choice
    
    # Fiscal Year Filter
    selected_year = st.selectbox(
        "Fiscal Year Filter",
        ["All Years", "2026", "2025", "2024", "2023", "2022"],
        index=0
    )
    year_val: Optional[int] = int(selected_year) if (selected_year is not None and selected_year != "All Years") else None
    
    # Fiscal Period Filter
    selected_period = st.selectbox(
        "Fiscal Period Filter",
        ["All Periods", "Q1", "Q2", "Q3", "Q4", "FY"],
        index=0
    )
    period_val = selected_period if (selected_period != "All Periods") else None
    
    st.markdown("---")
    
    # Execution Mode Selection
    query_mode = st.radio(
        "Execution Mode",
        [
            "Automatic Router",
            "Numeric (DuckDB SQL)",
            "Narrative (Hybrid Search)",
            "Contradiction Pass (MD&A vs Footnotes)",
            "Restatement Audit (Revision History)",
            "📋 Full Audit Report"
        ],
        index=0,
        help="Automatic Router classifies query into the optimal pipeline. Full Audit Report runs ALL routes for a comprehensive analysis."
    )
    
    st.markdown("---")
    st.markdown("### 💡 Quick Presets")
    
    period_str = f"{selected_period} " if selected_period != "All Periods" else ""
    year_str = f"{selected_year} " if selected_year != "All Years" else ""
    time_filter = f"{period_str}{year_str}".strip()
    time_prefix = f"{time_filter} " if time_filter else ""
    
    if is_india:
        p1_text = f"What was {selected_ticker} {time_prefix}Revenue / Turnover?".replace("  ", " ")
        p2_text = f"What are the promoter pledge, NPA, and regulatory risks for {selected_ticker}?"
        p3_text = f"Check if {selected_ticker} MD&A claims contradict Notes to Accounts"
        p4_text = f"Did {selected_ticker} restate revenue figures across filings?"

        def set_preset_1():
            st.session_state.user_query_input = p1_text

        def set_preset_2():
            st.session_state.user_query_input = p2_text

        def set_preset_3():
            st.session_state.user_query_input = p3_text

        def set_preset_4():
            st.session_state.user_query_input = p4_text

        st.button(f"📊 {selected_ticker} Turnover Metric", on_click=set_preset_1, use_container_width=True)
        st.button(f"⚠️ {selected_ticker} Promoter / NPA Risks", on_click=set_preset_2, use_container_width=True)
        st.button(f"🔍 {selected_ticker} MD&A vs Notes", on_click=set_preset_3, use_container_width=True)
        st.button(f"📜 {selected_ticker} Restatement Audit", on_click=set_preset_4, use_container_width=True)
    else:
        p1_text = f"What was {selected_ticker} {time_prefix}Revenue?".replace("  ", " ")
        p2_text = f"What are the key supply chain risks for {selected_ticker}?"
        p3_text = f"Check if {selected_ticker} Item 7 revenue claims contradict Item 8 footnotes"
        p4_text = f"Did {selected_ticker} restate revenue figures across filings?"

        def set_preset_1():
            st.session_state.user_query_input = p1_text

        def set_preset_2():
            st.session_state.user_query_input = p2_text

        def set_preset_3():
            st.session_state.user_query_input = p3_text

        def set_preset_4():
            st.session_state.user_query_input = p4_text

        st.button(f"📊 {selected_ticker} Revenue Metric", on_click=set_preset_1, use_container_width=True)
        st.button(f"⚠️ {selected_ticker} Risk Factors", on_click=set_preset_2, use_container_width=True)
        st.button(f"🔍 {selected_ticker} MD&A vs Footnotes", on_click=set_preset_3, use_container_width=True)
        st.button(f"📜 {selected_ticker} Restatement Audit", on_click=set_preset_4, use_container_width=True)


# ---------------------------------------------------------------------------
# FULL AUDIT REPORT HELPER
# ---------------------------------------------------------------------------
_FULL_AUDIT_METRICS = ["revenue", "net_income", "gross_profit", "total_assets", "cash", "operating_cash_flow"]
_FULL_AUDIT_METRIC_LABELS = {
    "revenue": "Revenue",
    "net_income": "Net Income",
    "gross_profit": "Gross Profit",
    "total_assets": "Total Assets",
    "cash": "Cash & Equivalents",
    "operating_cash_flow": "Operating Cash Flow",
}


def _run_full_audit(ticker: str, year_val: Optional[int], period_val: Optional[str], market: Optional[str] = None) -> Dict[str, Any]:
    """Runs all routes for a comprehensive Full Audit Report across US or Indian markets."""
    if not market:
        market = detect_market(ticker)
    ticker = normalize_ticker(ticker, market)

    _ensure_ticker_ingested(ticker, db_engine, hybrid_engine, market=market)

    # 1. Numeric: query all core metrics
    metric_results: Dict[str, pd.DataFrame] = {}
    for metric_key in _FULL_AUDIT_METRICS:
        df = db_engine.query_metric(ticker=ticker, concept=metric_key, year=year_val, period=period_val, market=market)
        metric_results[metric_key] = df

    # 2. Restatement: check revenue restatements
    restatement_df = db_engine.detect_restatements(ticker=ticker, concept="revenue", year=year_val)

    # 3. Narrative: general risk search
    narrative_results = hybrid_engine.search(
        query=f"key risks and financial outlook for {ticker}",
        top_k=5, ticker_filter=ticker
    )

    # 4. Contradiction: MD&A vs Footnotes / Notes to Accounts
    contradiction_result = verifier.verify(
        query=f"{ticker} revenue growth outlook and financial performance",
        ticker=ticker, top_k=4, market=market
    )

    return {
        "ticker": ticker,
        "market": market,
        "metric_results": metric_results,
        "restatement_df": restatement_df,
        "narrative_results": narrative_results,
        "contradiction_result": contradiction_result,
    }


def _render_full_audit_report(full_audit: Dict[str, Any]):
    """Renders the Full Audit Report tab: Summary → KPIs → Tables → Charts (all full-width)."""
    ticker = full_audit["ticker"]
    market = full_audit.get("market") or detect_market(ticker)
    is_india = (market == MARKET_INDIA or market == "INDIA")
    metric_results = full_audit["metric_results"]
    market_badge = "🇮🇳 NSE / Ind-AS" if is_india else "🇺🇸 SEC / US-GAAP"

    st.markdown(f"""
    <div style="margin-bottom: 14px;">
        <span class="badge-full-audit">📋 FULL AUDIT REPORT</span>
        <span style="color: #a5f3fc; font-weight: 600; font-size: 0.88rem; margin-left: 8px;">Target: {ticker} ({market_badge})</span>
    </div>
    """, unsafe_allow_html=True)

    # ---- EXECUTIVE SUMMARY (text above tables) ----
    available_metrics = {}
    for mk in _FULL_AUDIT_METRICS:
        df = metric_results.get(mk, pd.DataFrame())
        if isinstance(df, pd.DataFrame) and not df.empty:
            available_metrics[mk] = df["val"].iloc[0]

    revenue_str = format_value(available_metrics.get("revenue"), market=market) if "revenue" in available_metrics else "N/A"
    net_income_str = format_value(available_metrics.get("net_income"), market=market) if "net_income" in available_metrics else "N/A"
    total_assets_str = format_value(available_metrics.get("total_assets"), market=market) if "total_assets" in available_metrics else "N/A"
    cash_str = format_value(available_metrics.get("cash"), market=market) if "cash" in available_metrics else "N/A"

    # Restatement status
    restatement_df = full_audit.get("restatement_df")
    if isinstance(restatement_df, pd.DataFrame) and not restatement_df.empty:
        has_restatements = True
        restate_status = f"🚨 **{len(restatement_df)} restatement(s) detected**"
    else:
        has_restatements = False
        restate_status = "✅ No restatements detected"

    # Contradiction status
    contradiction = full_audit.get("contradiction_result", {})
    severity = contradiction.get("severity", "none")
    if severity == "contradiction":
        contra_status = f"🚨 **Material Discrepancy Detected** — {'Notes to Accounts contradict MD&A' if is_india else 'Footnotes contradict MD&A narrative'}"
    elif severity == "qualification":
        contra_status = f"⚠️ **Qualifying Disclosure** — {'Notes to Accounts temper management claims' if is_india else 'Footnotes temper management claims'}"
    else:
        contra_status = f"✅ No material contradiction — {'Notes to Accounts align with MD&A' if is_india else 'Footnotes align with MD&A'}"

    rev_label = "turnover / revenue" if is_india else "revenue"
    st.markdown(f"""
    <div class="panel-card">
        <div style="color: #34d399; font-weight: 700; font-size: 1.1rem; margin-bottom: 10px;">📝 Executive Summary — {ticker} ({market_badge})</div>
        <p style="color: #e2e8f0; font-size: 0.93rem; line-height: 1.7; margin: 0;">
            <strong>{ticker}</strong> reports <strong style="color: #34d399;">{revenue_str}</strong> in {rev_label},
            <strong style="color: #3b82f6;">{net_income_str}</strong> net income / PAT,
            total assets of <strong style="color: #f59e0b;">{total_assets_str}</strong>,
            and cash holdings of <strong style="color: #06b6d4;">{cash_str}</strong>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"**Restatement Status:** {restate_status}")
    st.markdown(f"**Contradiction Status:** {contra_status}")

    st.markdown("---")

    # ---- KPI CARDS (3 per row to prevent truncation) ----
    st.markdown("#### 💰 Financial Overview")
    metrics_list = list(_FULL_AUDIT_METRICS)

    # Row 1: first 3 metrics
    kpi_row1 = st.columns(3)
    for idx in range(min(3, len(metrics_list))):
        mk = metrics_list[idx]
        df = metric_results.get(mk, pd.DataFrame())
        label = _FULL_AUDIT_METRIC_LABELS.get(mk, mk)
        if isinstance(df, pd.DataFrame) and not df.empty:
            val = df["val"].iloc[0]
            period_info = f"{df['fiscal_year'].iloc[0]} {df['fiscal_period'].iloc[0]}"
            kpi_row1[idx].metric(label=label, value=format_value(val, market=market), delta=period_info)
        else:
            kpi_row1[idx].metric(label=label, value="N/A", delta="No data")

    # Row 2: next 3 metrics
    if len(metrics_list) > 3:
        kpi_row2 = st.columns(3)
        for idx in range(3, min(6, len(metrics_list))):
            mk = metrics_list[idx]
            df = metric_results.get(mk, pd.DataFrame())
            label = _FULL_AUDIT_METRIC_LABELS.get(mk, mk)
            col_idx = idx - 3
            if isinstance(df, pd.DataFrame) and not df.empty:
                val = df["val"].iloc[0]
                period_info = f"{df['fiscal_year'].iloc[0]} {df['fiscal_period'].iloc[0]}"
                kpi_row2[col_idx].metric(label=label, value=format_value(val, market=market), delta=period_info)
            else:
                kpi_row2[col_idx].metric(label=label, value="N/A", delta="No data")

    st.markdown("---")

    # ---- FINANCIAL SUMMARY TABLE ----
    st.markdown("#### 📅 Financial Summary Table")
    summary_rows = []
    tag_col_name = "Ind-AS / Statement Tag" if is_india else "US-GAAP Tag"
    for metric_key in _FULL_AUDIT_METRICS:
        df = metric_results.get(metric_key, pd.DataFrame())
        label = _FULL_AUDIT_METRIC_LABELS.get(metric_key, metric_key)
        if isinstance(df, pd.DataFrame) and not df.empty:
            for _, row in df.iterrows():
                summary_rows.append({
                    "Metric": label,
                    "Year": row.get("fiscal_year", ""),
                    "Period": row.get("fiscal_period", ""),
                    "Value": format_value(row.get("val"), market=market),
                    tag_col_name: row.get("concept", ""),
                    "Period Start": row.get("period_start", ""),
                    "Period End": row.get("period_end", ""),
                })

    if summary_rows:
        summary_df = pd.DataFrame(summary_rows)
        display_cols = ["Metric", "Year", "Period", "Value", tag_col_name, "Period Start", "Period End"]
        st.dataframe(summary_df[display_cols], use_container_width=True, hide_index=True, height=400)
    else:
        st.warning("No financial data available.")

    # ---- RESTATEMENT TABLE ----
    st.markdown("#### 📜 Restatement & Revision Analysis")
    if has_restatements and isinstance(restatement_df, pd.DataFrame) and not restatement_df.empty:
        st.markdown("""
        <div class="alert-qualification">
            <strong style="color: #fcd34d; font-size: 1.05rem;">🚨 REVISED FIGURES / RESTATEMENTS DETECTED</strong>
        </div>
        """, unsafe_allow_html=True)

        restate_display = restatement_df.copy()
        restate_display["Original"] = restate_display["original_val"].apply(lambda v: format_value(v, market=market))
        restate_display["Latest"] = restate_display["latest_val"].apply(lambda v: format_value(v, market=market))
        restate_display["Variance"] = restate_display["variance_usd"].apply(lambda v: format_value(v, market=market))
        restate_display["Δ%"] = restate_display["variance_pct"].apply(lambda v: f"{v:+.2f}%")
        restate_display["Revisions"] = restate_display.get("revision_count", 0)

        display_cols_r = ["fiscal_year", "fiscal_period", "concept", "Original", "Latest", "Variance", "Δ%", "Revisions"]
        rename_map_r = {"fiscal_year": "Year", "fiscal_period": "Period", "concept": "Concept"}
        cols_present_r = [c for c in display_cols_r if c in restate_display.columns]
        st.dataframe(restate_display[cols_present_r].rename(columns=rename_map_r), use_container_width=True, hide_index=True)  # type: ignore
    else:
        st.success("✅ No figure revisions or restatements detected for revenue.")

    # ---- CONTRADICTION TABLE / ANALYSIS ----
    section_label_contra = "MD&A vs Notes to Accounts" if is_india else "MD&A vs Footnote"
    st.markdown(f"#### ⚖️ {section_label_contra} Contradiction Analysis")
    mode_used = contradiction.get("verifier_mode", "Rule-based")

    if severity == "contradiction":
        st.markdown(f"""
        <div class="alert-contradiction">
            <strong style="color: #fca5a5; font-size: 1.05rem;">🚨 MATERIAL DISCREPANCY DETECTED</strong>
            <p style="color: #fbcfe8; margin: 4px 0 0 0;">{'Notes to Accounts' if is_india else 'Footnotes'} contain significant risk signals qualifying executive narrative claims.</p>
        </div>
        """, unsafe_allow_html=True)
    elif severity == "qualification":
        st.markdown(f"""
        <div class="alert-qualification">
            <strong style="color: #fcd34d; font-size: 1.05rem;">⚠️ QUALIFYING DISCLOSURE</strong>
            <p style="color: #fef3c7; margin: 4px 0 0 0;">{'Notes to Accounts' if is_india else 'Footnotes'} contain qualifying language that tempers management outlook.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-none">
            <strong style="color: #6ee7b7; font-size: 1.05rem;">✅ NO MATERIAL CONTRADICTION DETECTED</strong>
            <p style="color: #a7f3d0; margin: 4px 0 0 0;">{'Notes to Accounts align with MD&A disclosures.' if is_india else 'Footnotes align with Item 7 MD&A narrative disclosures.'}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"**Verifier Mode:** `{mode_used}`")
    st.write(contradiction.get("analysis", ""))

    risk_signals = contradiction.get("risk_signals_found", [])
    if risk_signals:
        st.markdown("##### 🚩 Detected Risk Signal Terms")
        tags_html = "".join([f'<span class="risk-tag">{sig.upper()}</span>' for sig in risk_signals])
        st.markdown(f"<div>{tags_html}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================
    # CHARTS SECTION (at the bottom, after all tables)
    # ============================================================
    st.markdown("## 📈 Visualizations")

    # Chart 1: Revenue Trend
    revenue_df = metric_results.get("revenue", pd.DataFrame())
    if isinstance(revenue_df, pd.DataFrame) and len(revenue_df) > 1:
        st.markdown("#### Revenue Trend by Period")
        chart_df = revenue_df.sort_values(by=["fiscal_year", "fiscal_period"]).copy()
        chart_df["period_label"] = chart_df["fiscal_year"].astype(str) + " " + chart_df["fiscal_period"]
        chart_df["formatted_val"] = chart_df["val"].apply(lambda v: format_value(v, market=market))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_df["period_label"],
            y=chart_df["val"],
            text=chart_df["formatted_val"],
            textposition="outside",
            textfont=dict(color="#34d399", size=12, family="Inter"),
            marker=dict(
                color=chart_df["val"],
                colorscale=[[0, "#065f46"], [0.5, "#10b981"], [1, "#34d399"]],
                line=dict(width=1, color="#10b981"),
            ),
            hovertemplate="<b>%{x}</b><br>Revenue: %{text}<extra></extra>",
        ))
        y_axis_label = "Revenue (₹ INR)" if is_india else "Revenue (USD)"
        _plotly_dark_layout(fig, title="Revenue by Period", y_title=y_axis_label, x_title="Fiscal Period")
        fig.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig, use_container_width=True, key="full_audit_revenue_chart")

    # Chart 2: Multi-Metric Comparison
    comparison_data = []
    for metric_key in _FULL_AUDIT_METRICS:
        df = metric_results.get(metric_key, pd.DataFrame())
        label = _FULL_AUDIT_METRIC_LABELS.get(metric_key, metric_key)
        if isinstance(df, pd.DataFrame) and not df.empty:
            latest_val = df["val"].iloc[0]
            comparison_data.append({"Metric": label, "Value": latest_val, "Formatted": format_value(latest_val, market=market)})

    if len(comparison_data) > 1:
        st.markdown(f"#### {ticker} — Latest Reported Metrics Comparison")
        comp_df = pd.DataFrame(comparison_data)
        fig_comp = go.Figure()
        colors = ["#10b981", "#3b82f6", "#8b5cf6", "#f59e0b", "#06b6d4", "#ec4899"]
        fig_comp.add_trace(go.Bar(
            x=comp_df["Metric"],
            y=comp_df["Value"],
            text=comp_df["Formatted"],
            textposition="outside",
            textfont=dict(color="#e2e8f0", size=11),
            marker=dict(color=colors[:len(comp_df)], line=dict(width=1, color="#334155")),
            hovertemplate="<b>%{x}</b><br>Value: %{text}<extra></extra>",
        ))
        y_axis_comp = "INR (₹)" if is_india else "USD ($)"
        _plotly_dark_layout(fig_comp, title=f"{ticker} — Latest Financial Metrics", y_title=y_axis_comp)
        fig_comp.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_comp, use_container_width=True, key="full_audit_metric_comparison")

    # Chart 3: Restatement bars (if any)
    if has_restatements and isinstance(restatement_df, pd.DataFrame) and not restatement_df.empty:
        st.markdown("#### Original vs Latest Reported Values")
        labels = restatement_df["fiscal_year"].astype(str) + " " + restatement_df["fiscal_period"]
        fig_restate = go.Figure()
        fig_restate.add_trace(go.Bar(
            name="Original Reported",
            x=labels, y=restatement_df["original_val"],
            text=restatement_df["original_val"].apply(lambda v: format_value(v, market=market)),
            textposition="outside", textfont=dict(size=10, color="#fde68a"),
            marker_color="#f59e0b",
            hovertemplate="<b>%{x}</b><br>Original: %{text}<extra></extra>",
        ))
        fig_restate.add_trace(go.Bar(
            name="Latest Reported",
            x=labels, y=restatement_df["latest_val"],
            text=restatement_df["latest_val"].apply(lambda v: format_value(v, market=market)),
            textposition="outside", textfont=dict(size=10, color="#6ee7b7"),
            marker_color="#10b981",
            hovertemplate="<b>%{x}</b><br>Latest: %{text}<extra></extra>",
        ))
        fig_restate.update_layout(barmode="group")
        y_axis_restate = "Value (INR)" if is_india else "Value (USD)"
        _plotly_dark_layout(fig_restate, title="Restatement Variance", y_title=y_axis_restate, x_title="Period")
        fig_restate.update_yaxes(tickformat=",.0f")
        st.plotly_chart(fig_restate, use_container_width=True, key="full_audit_restatement_chart")

    # Chart 4: Risk signal gauge (if any)
    if risk_signals:
        st.markdown("#### Risk Signal Severity")
        risk_count = len(risk_signals)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_count,
            title={"text": "Risk Signal Count", "font": {"color": "#e2e8f0", "size": 14}},
            number={"font": {"color": "#fca5a5", "size": 28}},
            gauge=dict(
                axis=dict(range=[0, max(10, risk_count + 2)], tickfont=dict(color="#94a3b8")),
                bar=dict(color="#ef4444"),
                bgcolor="rgba(15, 23, 42, 0.5)",
                bordercolor="#334155",
                steps=[
                    dict(range=[0, 2], color="rgba(6, 78, 59, 0.6)"),
                    dict(range=[2, 5], color="rgba(120, 53, 15, 0.6)"),
                    dict(range=[5, max(10, risk_count + 2)], color="rgba(131, 24, 67, 0.6)"),
                ],
                threshold=dict(line=dict(color="#fca5a5", width=3), thickness=0.8, value=risk_count),
            ),
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(15, 23, 42, 0.9)",
            plot_bgcolor="rgba(15, 23, 42, 0.5)",
            font=dict(color="#cbd5e1"),
            height=250,
            margin=dict(l=30, r=30, t=40, b=20),
        )
        st.plotly_chart(fig_gauge, use_container_width=True, key="full_audit_risk_gauge")


def _render_full_audit_citations(full_audit: Dict[str, Any]):
    """Renders the Full Audit Citations & Source Inspector tab (separate page)."""
    ticker = full_audit["ticker"]
    market = full_audit.get("market") or detect_market(ticker)
    is_india = (market == MARKET_INDIA or market == "INDIA")
    metric_results = full_audit["metric_results"]
    contradiction = full_audit.get("contradiction_result", {})

    # Market-specific Regulatory / Financial Link
    if is_india:
        quote_url = f"https://finance.yahoo.com/quote/{ticker}"
        st.markdown(f"""
        <div style="margin-bottom: 16px;">
            <a href="{quote_url}" target="_blank" class="edgar-link-btn">🔗 View {ticker} Live Market Profile & Financials on Yahoo Finance ↗</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        edgar_url = f"https://www.sec.gov/edgar/browse/?CIK={ticker}"
        st.markdown(f"""
        <div style="margin-bottom: 16px;">
            <a href="{edgar_url}" target="_blank" class="edgar-link-btn">🔗 View {ticker} Official SEC EDGAR Filing Page ↗</a>
        </div>
        """, unsafe_allow_html=True)

    # XBRL / Financial Statement Provenance
    prov_title = "🏛️ NSE / Ind-AS Financial Statement Provenance" if is_india else "🏛️ SEC EDGAR XBRL Tag Provenance"
    tag_label = "Ind-AS / Metric Tag:" if is_india else "Concept Tag:"
    st.markdown(f"#### 🗄️ DuckDB {prov_title}")
    revenue_df = metric_results.get("revenue", pd.DataFrame())
    if isinstance(revenue_df, pd.DataFrame) and not revenue_df.empty:
        first_row = revenue_df.iloc[0]
        form_label = first_row.get('form', 'Annual Report') if is_india else first_row.get('form', '10-K')
        st.markdown(f"""
        <div class="panel-card">
            <div style="color: #34d399; font-weight: 600;">{prov_title}</div>
            <p style="font-size: 0.87rem; color: #e2e8f0; margin-top: 8px;">
                <strong>Ticker:</strong> {ticker} ({'NSE/BSE' if is_india else 'SEC'})<br/>
                <strong>{tag_label}</strong> <code>{first_row.get('concept')}</code><br/>
                <strong>Filing / Form:</strong> {form_label} ({first_row.get('fiscal_year')} {first_row.get('fiscal_period')})<br/>
                <strong>Period Dates:</strong> {first_row.get('period_start', 'N/A')} to {first_row.get('period_end', 'N/A')}
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Pass A: Narrative Claims
    pass_a_label = "📘 Pass A: Management Discussion & Analysis (MD&A) Passages" if is_india else "#### 📘 Pass A: Item 7 (MD&A) Passages"
    st.markdown(pass_a_label if pass_a_label.startswith("#") else f"#### {pass_a_label}")
    narrative_claims = contradiction.get("narrative_claims", [])
    if narrative_claims:
        for idx, nc in enumerate(narrative_claims, 1):
            with st.expander(f"MD&A #{idx} — {nc.get('citation')}", expanded=(idx == 1)):
                st.write(nc.get("text"))
    else:
        st.info("No MD&A passages retrieved.")

    st.markdown("---")

    # Pass B: Disclosures / Footnotes
    pass_b_label = "📙 Pass B: Notes to Accounts & Auditor's Report Passages" if is_india else "#### 📙 Pass B: Item 8 (Footnotes) Passages"
    st.markdown(pass_b_label if pass_b_label.startswith("#") else f"#### {pass_b_label}")
    footnote_disclosures = contradiction.get("footnote_disclosures", [])
    if footnote_disclosures:
        for idx, fd in enumerate(footnote_disclosures, 1):
            with st.expander(f"Disclosure #{idx} — {fd.get('citation')}", expanded=(idx == 1)):
                st.write(fd.get("text"))
    else:
        st.info(f"No {'Notes to Accounts' if is_india else 'Item 8 (Footnote)'} passages retrieved.")

    st.markdown("---")

    # Narrative Risk Passages
    st.markdown("#### 🔍 Key Risk Factor Passages")
    narrative_results = full_audit.get("narrative_results", [])
    if narrative_results:
        for idx, item in enumerate(narrative_results, 1):
            with st.expander(f"Passage #{idx} — {item.get('citation')} (Score: {item.get('score', 0):.4f})", expanded=(idx == 1)):
                st.markdown(f"**Section**: `{item.get('section_key')}` | **Title**: {item.get('item_title')}")
                st.write(item.get("text"))
    else:
        st.info("No narrative risk passages found.")


# ---------------------------------------------------------------------------
# MAIN AREA: Query Input (always full-width)
# ---------------------------------------------------------------------------
st.markdown("### 📊 Audit Findings & Analysis")

raw_query = st.text_area(
    "Audit Question",
    key="user_query_input",
    height=90,
    help="Type any metric query, qualitative search, restatement inquiry, or contradiction audit"
)
user_query: str = raw_query or ""

run_btn = st.button("🚀 Run Forensic Audit Engine", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Execute Audit Pipeline on Button Click
# ---------------------------------------------------------------------------
if run_btn:
    is_full_audit = (query_mode == "📋 Full Audit Report")

    if is_full_audit:
        with st.spinner(f"Running Full Audit Report for {selected_ticker}..."):
            ticker_target: str = str(selected_ticker)
            full_audit_data = _run_full_audit(ticker_target, year_val, period_val, market=current_market)
            st.session_state.audit_results = {
                "query": f"Full Audit Report for {ticker_target}",
                "route_type": "FULL_AUDIT",
                "ticker": ticker_target,
                "market": current_market,
                "full_audit": full_audit_data,
            }
    else:
        with st.spinner(f"Executing forensic audit pipeline for {selected_ticker}..."):
            ticker_target: str = str(selected_ticker)

            # Route query
            route_meta = router.route_query(user_query)
            route_type = route_meta["route_type"]

            # Override route if explicit mode chosen
            if query_mode == "Numeric (DuckDB SQL)":
                route_type = QueryType.NUMERIC
            elif query_mode == "Narrative (Hybrid Search)":
                route_type = QueryType.NARRATIVE
            elif query_mode == "Contradiction Pass (MD&A vs Footnotes)":
                route_type = QueryType.CONTRADICTION
            elif query_mode == "Restatement Audit (Revision History)":
                route_type = QueryType.RESTATEMENT

            # Check ticker override from natural language text (BUG-3 FIX)
            raw_ticker = route_meta.get("ticker")
            if selected_ticker and raw_ticker and raw_ticker.upper() != selected_ticker.upper():
                ticker_target = raw_ticker.upper()

            # Determine market for query
            market_for_query = route_meta.get("market") or detect_market(ticker_target) or current_market
            ticker_target = normalize_ticker(ticker_target, market_for_query)

            # Ensure data is ingested
            _ensure_ticker_ingested(ticker_target, db_engine, hybrid_engine, market=market_for_query)

            results_payload: Dict[str, Any] = {
                "query": user_query,
                "route_meta": route_meta,
                "route_type": route_type,
                "ticker": ticker_target,
                "market": market_for_query,
                "df_result": None,
                "restatement_result": None,
                "narrative_results": [],
                "verification_result": None
            }

            # Execute Action based on Route
            if route_type == QueryType.NUMERIC:
                raw_concept = route_meta.get("concept")
                concept: str = str(raw_concept) if raw_concept else "revenue"
                yr: Optional[int] = route_meta.get("fiscal_year") or year_val
                prd: Optional[str] = route_meta.get("fiscal_period") or period_val

                df = db_engine.query_metric(ticker=ticker_target, concept=concept, year=yr, period=prd, market=market_for_query)
                results_payload["df_result"] = df

            elif route_type == QueryType.RESTATEMENT:
                raw_concept = route_meta.get("concept")
                concept: str = str(raw_concept) if raw_concept else "revenue"
                yr: Optional[int] = route_meta.get("fiscal_year") or year_val

                df_restate = db_engine.detect_restatements(ticker=ticker_target, concept=concept, year=yr)
                results_payload["restatement_result"] = df_restate

            elif route_type == QueryType.NARRATIVE:
                raw_sec = route_meta.get("section_filter")
                sec_filter: Optional[str] = str(raw_sec) if raw_sec else None

                n_results = hybrid_engine.search(
                    query=user_query,
                    top_k=5,
                    ticker_filter=ticker_target,
                    section_filter=sec_filter
                )
                results_payload["narrative_results"] = n_results

            elif route_type == QueryType.CONTRADICTION:
                ver_result = verifier.verify(query=user_query, ticker=ticker_target, top_k=4, market=market_for_query)
                results_payload["verification_result"] = ver_result

            st.session_state.audit_results = results_payload


# ---------------------------------------------------------------------------
# RENDER RESULTS: Full Audit → Full Width + Tabs | Other → 2-Column
# ---------------------------------------------------------------------------
if st.session_state.audit_results is None:
    st.info("👈 Select options on the left and click **🚀 Run Forensic Audit Engine**.")
else:
    res = st.session_state.audit_results
    route_type = res["route_type"]
    res_market = res.get("market") or detect_market(res.get("ticker", ""))
    is_res_india = (res_market == MARKET_INDIA or res_market == "INDIA")
    market_tag = "🇮🇳 NSE / Ind-AS" if is_res_india else "🇺🇸 SEC / US-GAAP"

    # =======================================================================
    # FULL AUDIT REPORT: Full-width with 2 tabs (Report | Citations)
    # =======================================================================
    if route_type == "FULL_AUDIT":
        tab_report, tab_citations = st.tabs(["📊 Audit Report", "📄 Source Citations & Inspector"])

        with tab_report:
            _render_full_audit_report(res["full_audit"])

        with tab_citations:
            _render_full_audit_citations(res["full_audit"])

    # =======================================================================
    # SINGLE-ROUTE MODES: Keep 2-column layout (Findings | Citations)
    # =======================================================================
    else:
        col_mid, col_right = st.columns([1.8, 1.4])

        with col_mid:
            # NUMERIC ROUTE DISPLAY
            if route_type == QueryType.NUMERIC:
                st.markdown(f"""
                <div style="margin-bottom: 14px;">
                    <span class="badge-numeric">⚡ ROUTE: NUMERIC (DuckDB SQL Engine)</span>
                    <span style="color: #34d399; font-weight: 600; font-size: 0.88rem; margin-left: 8px;">Target: {res['ticker']} ({market_tag})</span>
                </div>
                """, unsafe_allow_html=True)

                df = res.get("df_result")
                if isinstance(df, pd.DataFrame) and not df.empty:
                    first_val = df["val"].iloc[0]
                    tag_name = "Ind-AS Tag" if is_res_india else "US-GAAP Tag"

                    st.metric(
                        label=f"Latest Reported Value ({df['fiscal_year'].iloc[0]} {df['fiscal_period'].iloc[0]})",
                        value=format_value(first_val, market=res_market),
                        delta=f"{tag_name}: {df['concept'].iloc[0]}"
                    )

                    display_df = df.sort_values(by=["fiscal_year", "fiscal_period"], ascending=[False, False]).copy()
                    display_df["Value"] = display_df["val"].apply(lambda v: format_value(v, market=res_market))
                    cols_to_show = ["fiscal_year", "fiscal_period", "label", "Value", "period_start", "period_end"]
                    cols_present = [c for c in cols_to_show if c in display_df.columns]

                    rename_map = {"fiscal_year": "Year", "fiscal_period": "Period", "label": "Metric"}
                    st.markdown("#### 📅 Data Table")
                    st.dataframe(display_df[cols_present].rename(columns=rename_map), use_container_width=True, hide_index=True)  # type: ignore[call-overload]

                    # Plotly bar chart if multiple entries
                    if len(df) > 1 and "val" in df.columns:
                        st.markdown("#### 📈 Multi-Period Trend")
                        df_sorted = df.sort_values(by=["fiscal_year", "fiscal_period"]).copy()
                        df_sorted["period_label"] = df_sorted["fiscal_year"].astype(str) + " " + df_sorted["fiscal_period"]
                        df_sorted["formatted_val"] = df_sorted["val"].apply(lambda v: format_value(v, market=res_market))

                        fig = go.Figure()
                        fig.add_trace(go.Bar(
                            x=df_sorted["period_label"],
                            y=df_sorted["val"],
                            text=df_sorted["formatted_val"],
                            textposition="outside",
                            textfont=dict(color="#34d399", size=12, family="Inter"),
                            marker=dict(
                                color=df_sorted["val"],
                                colorscale=[[0, "#065f46"], [0.5, "#10b981"], [1, "#34d399"]],
                                line=dict(width=1, color="#10b981"),
                            ),
                            hovertemplate="<b>%{x}</b><br>Value: %{text}<extra></extra>",
                        ))
                        y_axis_name = "Value (INR)" if is_res_india else "Value (USD)"
                        _plotly_dark_layout(fig, title="Value by Period", y_title=y_axis_name, x_title="Fiscal Period")
                        fig.update_yaxes(tickformat=",.0f")
                        st.plotly_chart(fig, use_container_width=True, key="numeric_trend_chart")
                else:
                    target_concept = str(res['route_meta'].get('concept') or 'revenue')
                    st.warning(f"No numeric facts found in DuckDB for **{res['ticker']}** with concept **{target_concept}**.")
                    try:
                        df_available = db_engine.query_metric(ticker=res['ticker'], concept=target_concept, year=None, period=None, market=res_market)
                        if isinstance(df_available, pd.DataFrame) and not df_available.empty:
                            avail_list = (
                                df_available[["fiscal_year", "fiscal_period"]]
                                .drop_duplicates()
                                .astype(str)
                                .apply(lambda r: f"{r['fiscal_period']} {r['fiscal_year']}", axis=1)
                                .tolist()
                            )
                            st.info(f"💡 **Available reported periods for {res['ticker']}**: {', '.join(avail_list[:8])}. Try querying one of these periods!")
                    except Exception:
                        pass

            # RESTATEMENT ROUTE DISPLAY
            elif route_type == QueryType.RESTATEMENT:
                st.markdown(f"""
                <div style="margin-bottom: 14px;">
                    <span class="badge-restatement">📜 ROUTE: RESTATEMENT AUDIT (Revision Engine)</span>
                    <span style="color: #fde68a; font-weight: 600; font-size: 0.88rem; margin-left: 8px;">Target: {res['ticker']} ({market_tag})</span>
                </div>
                """, unsafe_allow_html=True)

                df_restate = res.get("restatement_result")
                if isinstance(df_restate, pd.DataFrame) and not df_restate.empty:
                    st.markdown("""
                    <div class="alert-qualification">
                        <strong style="color: #fcd34d; font-size: 1.05rem;">🚨 REVISED FIGURES / RESTATEMENTS DETECTED</strong>
                        <p style="color: #fef3c7; margin: 4px 0 0 0; font-size: 0.9rem;">
                            This metric was reported with differing figures across multiple filing dates.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Summary table with formatted values
                    restate_display = df_restate.copy()
                    restate_display["Original"] = restate_display["original_val"].apply(lambda v: format_value(v, market=res_market))
                    restate_display["Latest"] = restate_display["latest_val"].apply(lambda v: format_value(v, market=res_market))
                    restate_display["Variance"] = restate_display["variance_usd"].apply(lambda v: format_value(v, market=res_market))
                    restate_display["Δ%"] = restate_display["variance_pct"].apply(lambda v: f"{v:+.2f}%")
                    restate_display["Revisions"] = restate_display.get("revision_count", 0)

                    st.markdown("#### 📅 Restatement Summary Table")
                    display_cols_r = ["fiscal_year", "fiscal_period", "concept", "Original", "Latest", "Variance", "Δ%", "Revisions"]
                    rename_map_r = {"fiscal_year": "Year", "fiscal_period": "Period", "concept": "Concept"}
                    cols_present_r = [c for c in display_cols_r if c in restate_display.columns]
                    st.dataframe(restate_display[cols_present_r].rename(columns=rename_map_r), use_container_width=True, hide_index=True)  # type: ignore

                    # Grouped bar chart: Original vs Latest
                    st.markdown("#### 📊 Original vs Latest Comparison")
                    labels = df_restate["fiscal_year"].astype(str) + " " + df_restate["fiscal_period"]
                    fig_restate = go.Figure()
                    fig_restate.add_trace(go.Bar(
                        name="Original Reported",
                        x=labels, y=df_restate["original_val"],
                        text=df_restate["original_val"].apply(lambda v: format_value(v, market=res_market)),
                        textposition="outside", textfont=dict(size=10, color="#fde68a"),
                        marker_color="#f59e0b",
                        hovertemplate="<b>%{x}</b><br>Original: %{text}<extra></extra>",
                    ))
                    fig_restate.add_trace(go.Bar(
                        name="Latest Reported",
                        x=labels, y=df_restate["latest_val"],
                        text=df_restate["latest_val"].apply(lambda v: format_value(v, market=res_market)),
                        textposition="outside", textfont=dict(size=10, color="#6ee7b7"),
                        marker_color="#10b981",
                        hovertemplate="<b>%{x}</b><br>Latest: %{text}<extra></extra>",
                    ))
                    fig_restate.update_layout(barmode="group")
                    y_axis_r = "Value (INR)" if is_res_india else "Value (USD)"
                    _plotly_dark_layout(fig_restate, title="Restatement Variance", y_title=y_axis_r, x_title="Period")
                    fig_restate.update_yaxes(tickformat=",.0f")
                    st.plotly_chart(fig_restate, use_container_width=True, key="restatement_comparison_chart")

                    # Variance % chart
                    if len(df_restate) > 0:
                        st.markdown("#### 📉 Variance Percentage by Period")
                        fig_var = go.Figure()
                        var_colors = ["#ef4444" if v < 0 else "#10b981" for v in df_restate["variance_pct"]]
                        fig_var.add_trace(go.Bar(
                            x=labels,
                            y=df_restate["variance_pct"],
                            text=df_restate["variance_pct"].apply(lambda v: f"{v:+.2f}%"),
                            textposition="outside",
                            textfont=dict(size=11, color="#e2e8f0"),
                            marker_color=var_colors,
                            hovertemplate="<b>%{x}</b><br>Variance: %{text}<extra></extra>",
                        ))
                        _plotly_dark_layout(fig_var, title="Percentage Shift per Period", y_title="Variance %", x_title="Period")
                        fig_var.add_hline(y=0, line_dash="dash", line_color="#64748b", line_width=1)
                        st.plotly_chart(fig_var, use_container_width=True, key="restatement_variance_pct_chart")
                else:
                    st.success(f"✅ No figure revisions or restatements detected for **{res['ticker']}** under concept **{res['route_meta'].get('concept') or 'revenue'}**.")

            # NARRATIVE ROUTE DISPLAY
            elif route_type == QueryType.NARRATIVE:
                st.markdown(f"""
                <div style="margin-bottom: 14px;">
                    <span class="badge-narrative">🔍 ROUTE: NARRATIVE (Section Hybrid Search)</span>
                    <span style="color: #93c5fd; font-weight: 600; font-size: 0.88rem; margin-left: 8px;">Target: {res['ticker']} ({market_tag})</span>
                </div>
                """, unsafe_allow_html=True)

                n_res = res.get("narrative_results", [])
                if n_res:
                    st.success(f"Retrieved **{len(n_res)}** re-ranked section passages:")

                    # Relevance score chart
                    if len(n_res) > 1:
                        st.markdown("#### 📊 Passage Relevance Scores")
                        passage_labels = [f"#{i+1} {item.get('section_key', '')}" for i, item in enumerate(n_res)]
                        passage_scores = [item.get("score", 0) for item in n_res]
                        fig_scores = go.Figure()
                        fig_scores.add_trace(go.Bar(
                            x=passage_scores, y=passage_labels,
                            orientation="h",
                            text=[f"{s:.4f}" for s in passage_scores],
                            textposition="auto",
                            textfont=dict(color="#e2e8f0", size=11),
                            marker=dict(
                                color=passage_scores,
                                colorscale=[[0, "#1e3a5f"], [0.5, "#3b82f6"], [1, "#93c5fd"]],
                                line=dict(width=1, color="#3b82f6"),
                            ),
                            hovertemplate="<b>%{y}</b><br>Score: %{x:.4f}<extra></extra>",
                        ))
                        _plotly_dark_layout(fig_scores, title="Re-rank Relevance Scores", x_title="Flashrank Score")
                        fig_scores.update_layout(height=max(200, len(n_res) * 45))
                        st.plotly_chart(fig_scores, use_container_width=True, key="narrative_scores_chart")

                    for idx, item in enumerate(n_res, 1):
                        with st.expander(f"Passage #{idx} — {item.get('citation')} (Re-rank Score: {item.get('score', 0):.4f})", expanded=(idx == 1)):
                            st.markdown(f"**Section**: `{item.get('section_key')}` | **Title**: {item.get('item_title')}")
                            st.write(item.get("text"))
                else:
                    st.warning(f"No matching section passages found for **{res['ticker']}**.")

            # CONTRADICTION ROUTE DISPLAY
            elif route_type == QueryType.CONTRADICTION:
                ver: Dict[str, Any] = res.get("verification_result", {})
                severity = ver.get("severity", "none")
                mode_used = ver.get("verifier_mode", "Rule-based")

                st.markdown(f"""
                <div style="margin-bottom: 14px;">
                    <span class="badge-contradiction">⚖️ ROUTE: CONTRADICTION (Dual-Pass Verifier)</span>
                    <span style="color: #fbcfe8; font-weight: 600; font-size: 0.88rem; margin-left: 8px;">Mode: {mode_used} | {market_tag}</span>
                </div>
                """, unsafe_allow_html=True)

                disc_name = "Notes to Accounts" if is_res_india else "Footnotes"
                if severity == "contradiction":
                    st.markdown(f"""
                    <div class="alert-contradiction">
                        <strong style="color: #fca5a5; font-size: 1.05rem;">🚨 MATERIAL DISCREPANCY DETECTED</strong>
                        <p style="color: #fbcfe8; margin: 4px 0 0 0;">{disc_name} contain significant risk signals qualifying executive narrative claims.</p>
                    </div>
                    """, unsafe_allow_html=True)
                elif severity == "qualification":
                    st.markdown(f"""
                    <div class="alert-qualification">
                        <strong style="color: #fcd34d; font-size: 1.05rem;">⚠️ QUALIFYING DISCLOSURE</strong>
                        <p style="color: #fef3c7; margin: 4px 0 0 0;">{disc_name} contain qualifying language that tempers management outlook.</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    align_desc = "Notes to Accounts align with MD&A disclosures." if is_res_india else "Footnotes align with Item 7 MD&A narrative disclosures."
                    st.markdown(f"""
                    <div class="alert-none">
                        <strong style="color: #6ee7b7; font-size: 1.05rem;">✅ NO MATERIAL CONTRADICTION DETECTED</strong>
                        <p style="color: #a7f3d0; margin: 4px 0 0 0;">{align_desc}</p>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("#### 🔬 Forensic Verifier Analysis")
                st.write(ver.get("analysis", ""))

                risk_signals = ver.get("risk_signals_found", [])
                if risk_signals:
                    st.markdown("#### 🚩 Detected Risk Signal Terms")
                    tags_html = "".join([f'<span class="risk-tag">{sig.upper()}</span>' for sig in risk_signals])
                    st.markdown(f"<div>{tags_html}</div>", unsafe_allow_html=True)

                    # Risk signal severity gauge
                    risk_count = len(risk_signals)
                    fig_gauge = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=risk_count,
                        title={"text": "Risk Signal Count", "font": {"color": "#e2e8f0", "size": 14}},
                        number={"font": {"color": "#fca5a5", "size": 28}},
                        gauge=dict(
                            axis=dict(range=[0, max(10, risk_count + 2)], tickfont=dict(color="#94a3b8")),
                            bar=dict(color="#ef4444"),
                            bgcolor="rgba(15, 23, 42, 0.5)",
                            bordercolor="#334155",
                            steps=[
                                dict(range=[0, 2], color="rgba(6, 78, 59, 0.6)"),
                                dict(range=[2, 5], color="rgba(120, 53, 15, 0.6)"),
                                dict(range=[5, max(10, risk_count + 2)], color="rgba(131, 24, 67, 0.6)"),
                            ],
                            threshold=dict(line=dict(color="#fca5a5", width=3), thickness=0.8, value=risk_count),
                        ),
                    ))
                    fig_gauge.update_layout(
                        paper_bgcolor="rgba(15, 23, 42, 0.9)",
                        plot_bgcolor="rgba(15, 23, 42, 0.5)",
                        font=dict(color="#cbd5e1"),
                        height=250,
                        margin=dict(l=30, r=30, t=40, b=20),
                    )
                    st.plotly_chart(fig_gauge, use_container_width=True, key="contradiction_risk_gauge")

        # ---------------------------------------------------------------
        # RIGHT PANEL: Citations & Source Inspector (non-Full Audit modes)
        # ---------------------------------------------------------------
        with col_right:
            st.markdown("### 📄 Source Citations & Inspector")

            ticker_sym = res["ticker"]

            # Market-specific Regulatory / Financial Link
            if is_res_india:
                quote_url = f"https://finance.yahoo.com/quote/{ticker_sym}"
                st.markdown(f"""
                <div style="margin-bottom: 16px;">
                    <a href="{quote_url}" target="_blank" class="edgar-link-btn">🔗 View {ticker_sym} Live Quotes & Financials on Yahoo Finance ↗</a>
                </div>
                """, unsafe_allow_html=True)
            else:
                edgar_url = f"https://www.sec.gov/edgar/browse/?CIK={ticker_sym}"
                st.markdown(f"""
                <div style="margin-bottom: 16px;">
                    <a href="{edgar_url}" target="_blank" class="edgar-link-btn">🔗 View {ticker_sym} Official SEC EDGAR Filing Page ↗</a>
                </div>
                """, unsafe_allow_html=True)

            if route_type == QueryType.CONTRADICTION:
                ver = res.get("verification_result", {})
                pass_a_hdr = "#### 📘 Pass A: Management Discussion & Analysis (MD&A) Passages" if is_res_india else "#### 📘 Pass A: Item 7 (MD&A) Passages"
                st.markdown(pass_a_hdr)
                for idx, nc in enumerate(ver.get("narrative_claims", []), 1):
                    with st.expander(f"MD&A #{idx} — {nc.get('citation')}"):
                        st.write(nc.get("text"))

                st.markdown("---")
                pass_b_hdr = "#### 📙 Pass B: Notes to Accounts & Auditor's Report Passages" if is_res_india else "#### 📙 Pass B: Item 8 (Footnotes) Passages"
                st.markdown(pass_b_hdr)
                for idx, fd in enumerate(ver.get("footnote_disclosures", []), 1):
                    with st.expander(f"Disclosure #{idx} — {fd.get('citation')}"):
                        st.write(fd.get("text"))

            elif route_type == QueryType.NARRATIVE:
                st.markdown("#### 📚 Document Citations")
                for item in res.get("narrative_results", []):
                    st.markdown(f"""
                    <div class="panel-card">
                        <div style="color: #34d399; font-weight: 600;">📍 {item.get('citation')}</div>
                        <p style="font-size: 0.85rem; color: #94a3b8; margin: 4px 0;">
                            <strong>Section:</strong> {item.get('item_title')}<br/>
                            <strong>Re-rank Score:</strong> {item.get('score', 0):.4f}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

            elif route_type in (QueryType.NUMERIC, QueryType.RESTATEMENT):
                prov_hdr = "🏛️ NSE / Ind-AS Financial Statement Fact Provenance" if is_res_india else "🏛️ SEC EDGAR XBRL Tag Provenance"
                tag_label_s = "Ind-AS / Metric Tag:" if is_res_india else "Concept Tag:"
                st.markdown(f"#### 🗄️ DuckDB {prov_hdr}")
                df = res.get("df_result") if route_type == QueryType.NUMERIC else res.get("restatement_result")
                if isinstance(df, pd.DataFrame) and not df.empty:
                    first_row = df.iloc[0]
                    form_val = first_row.get('form', 'Annual Report') if is_res_india else first_row.get('form', '10-K')
                    st.markdown(f"""
                    <div class="panel-card">
                        <div style="color: #34d399; font-weight: 600;">{prov_hdr}</div>
                        <p style="font-size: 0.87rem; color: #e2e8f0; margin-top: 8px;">
                            <strong>Ticker:</strong> {ticker_sym} ({'NSE/BSE' if is_res_india else 'SEC'})<br/>
                            <strong>{tag_label_s}</strong> <code>{first_row.get('concept')}</code><br/>
                            <strong>Filing / Form:</strong> {form_val} ({first_row.get('fiscal_year')} {first_row.get('fiscal_period')})<br/>
                            <strong>Period Dates:</strong> {first_row.get('period_start', 'N/A')} to {first_row.get('period_end', 'N/A')}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
