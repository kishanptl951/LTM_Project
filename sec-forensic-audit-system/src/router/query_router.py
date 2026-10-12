"""
Deterministic Query Router: Classifies user query into NUMERIC, NARRATIVE, or CONTRADICTION routes.
Extracts structured metadata (ticker, concept, fiscal_year, fiscal_period) from the query text
so downstream engines (DuckDB, HybridSearch) receive pre-parsed keys directly.
Supports both US (SEC EDGAR) and Indian (NSE/BSE) market tickers and terminology.
"""
import re
import logging
from enum import Enum
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class QueryType(Enum):
    NUMERIC = "numeric"
    NARRATIVE = "narrative"
    CONTRADICTION = "contradiction"
    RESTATEMENT = "restatement"


# US Company name mapping to ticker symbols
US_COMPANY_NAME_MAP: Dict[str, str] = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "resmed": "RMD",
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "nvidia": "NVDA",
    "microsoft": "MSFT",
    "google": "GOOG",
    "alphabet": "GOOG",
    "amazon": "AMZN",
    "meta": "META",
    "pfizer": "PFE",
    "boeing": "BA",
    "intel": "INTC",
    "amd": "AMD",
    "walmart": "WMT",
    "disney": "DIS",
    "netflix": "NFLX",
}

# Indian Company name mapping to ticker symbols (NSE)
INDIAN_COMPANY_NAME_MAP: Dict[str, str] = {
    "reliance": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "infosys": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS",
    "hdfcbank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "icicibank": "ICICIBANK.NS",
    "sbi": "SBIN.NS",
    "state bank": "SBIN.NS",
    "wipro": "WIPRO.NS",
    "airtel": "BHARTIARTL.NS",
    "bharti airtel": "BHARTIARTL.NS",
    "itc": "ITC.NS",
    "hul": "HINDUNILVR.NS",
    "hindustan unilever": "HINDUNILVR.NS",
    "kotak": "KOTAKBANK.NS",
    "kotak bank": "KOTAKBANK.NS",
    "adani": "ADANIENT.NS",
    "adani enterprises": "ADANIENT.NS",
    "bajaj finance": "BAJFINANCE.NS",
    "maruti": "MARUTI.NS",
    "maruti suzuki": "MARUTI.NS",
    "asian paints": "ASIANPAINT.NS",
    "titan": "TITAN.NS",
    "l&t": "LT.NS",
    "larsen": "LT.NS",
    "larsen & toubro": "LT.NS",
    "sun pharma": "SUNPHARMA.NS",
    "tata motors": "TATAMOTORS.NS",
    "tata steel": "TATASTEEL.NS",
    "axis bank": "AXISBANK.NS",
    "power grid": "POWERGRID.NS",
    "ntpc": "NTPC.NS",
    "ongc": "ONGC.NS",
    "coal india": "COALINDIA.NS",
    "ultratech": "ULTRACEMCO.NS",
    "tech mahindra": "TECHM.NS",
    "hcl tech": "HCLTECH.NS",
    "hcltech": "HCLTECH.NS",
    "dr reddy": "DRREDDY.NS",
    "bajaj finserv": "BAJAJFINSV.NS",
    "nestle india": "NESTLEIND.NS",
    "hero motocorp": "HEROMOTOCO.NS",
    "britannia": "BRITANNIA.NS",
    "jsw steel": "JSWSTEEL.NS",
    "hindalco": "HINDALCO.NS",
    "cipla": "CIPLA.NS",
    "grasim": "GRASIM.NS",
    "divis lab": "DIVISLAB.NS",
}

# Merged company name map (Indian checked first for priority)
COMPANY_NAME_MAP: Dict[str, str] = {**US_COMPANY_NAME_MAP, **INDIAN_COMPANY_NAME_MAP}

# ---------------------------------------------------------------------------
# Keyword dictionaries for concept extraction
# Maps natural-language terms to the canonical metric key used by DuckDB engine
# ---------------------------------------------------------------------------
CONCEPT_KEYWORDS: Dict[str, str] = {
    # Revenue variants
    "revenue": "revenue",
    "revenues": "revenue",
    "sales": "revenue",
    "top line": "revenue",
    "top-line": "revenue",
    "turnover": "revenue",           # Indian terminology
    # Net income variants
    "net income": "net_income",
    "net profit": "net_income",
    "bottom line": "net_income",
    "bottom-line": "net_income",
    "profit": "net_income",
    "earnings": "net_income",
    "pat": "net_income",             # Indian: Profit After Tax
    "profit after tax": "net_income",
    # Gross profit
    "gross profit": "gross_profit",
    "gross margin": "gross_profit",
    # Operating income
    "operating income": "operating_income",
    "operating profit": "operating_income",
    "ebit": "operating_income",
    "pbt": "operating_income",       # Indian: Profit Before Tax
    "profit before tax": "operating_income",
    # Balance sheet
    "total assets": "total_assets",
    "assets": "total_assets",
    "total liabilities": "total_liabilities",
    "liabilities": "total_liabilities",
    "debt": "total_liabilities",
    "cash": "cash",
    "cash and equivalents": "cash",
    # Operating cash flow
    "operating cash flow": "operating_cash_flow",
    "cash flow from operations": "operating_cash_flow",
    "cash from operations": "operating_cash_flow",
    "cash flow": "operating_cash_flow",
    # Capital expenditures
    "capital expenditures": "capital_expenditure",
    "capital expenditure": "capital_expenditure",
    "capex": "capital_expenditure",
    # R&D
    "research and development": "rnd_expense",
    "r&d": "rnd_expense",
    "rnd": "rnd_expense",
    # Operating expenses
    "operating expenses": "operating_expenses",
    "operating expense": "operating_expenses",
    "opex": "operating_expenses",
    # EPS
    "eps": "net_income",
    "earnings per share": "net_income",
    # Indian-specific
    "depreciation": "depreciation",
    "ebitda": "ebitda",
    "interest expense": "interest_expense",
    "tax expense": "tax_expense",
    "provisions": "operating_expenses",
    "npa": "total_liabilities",       # Non-Performing Assets (banking)
}

# Multi-word concepts must be checked before single-word ones.
# Sort by descending length so "net income" matches before "income".
_CONCEPT_KEYS_SORTED: List[str] = sorted(CONCEPT_KEYWORDS.keys(), key=len, reverse=True)

# Known tickers in the corpus (expandable — both US and Indian)
KNOWN_US_TICKERS = {"AAPL", "TSLA", "RMD", "JPM", "NVDA", "MSFT", "GOOG", "AMZN", "META"}
KNOWN_INDIAN_TICKERS = {
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "WIPRO.NS", "BHARTIARTL.NS", "ITC.NS", "HINDUNILVR.NS",
    "KOTAKBANK.NS", "ADANIENT.NS", "BAJFINANCE.NS", "MARUTI.NS",
    "ASIANPAINT.NS", "TITAN.NS", "LT.NS", "SUNPHARMA.NS",
    "TATAMOTORS.NS", "TATASTEEL.NS", "AXISBANK.NS", "POWERGRID.NS",
    "NTPC.NS", "ONGC.NS", "COALINDIA.NS", "ULTRACEMCO.NS",
    "TECHM.NS", "HCLTECH.NS", "DRREDDY.NS",
}
KNOWN_TICKERS = KNOWN_US_TICKERS | {t.replace(".NS", "") for t in KNOWN_INDIAN_TICKERS} | KNOWN_INDIAN_TICKERS

# Restatement intent keywords
RESTATEMENT_KEYWORDS = [
    "restate", "restatement", "restated", "revision", "revised", "revisions",
    "amended", "10-k/a", "10-q/a", "original vs", "original versus",
    "changed between filings", "accounting shift", "historical adjustment"
]

# Contradiction / audit intent keywords
CONTRADICTION_KEYWORDS = [
    "contradict", "contradiction", "discrepancy", "discrepancies",
    "mismatch", "inconsisten", "hidden risk", "buried",
    "item 7 vs item 8", "item 7 versus item 8",
    "md&a vs footnote", "md&a versus footnote",
    "narrative vs footnote", "narrative versus footnote",
    "footnote mismatch", "cross-check", "cross check",
    "verify", "verification", "audit", "forensic",
    "qualify", "qualifies",
]

# Numeric intent signal keywords (beyond concept matches)
NUMERIC_SIGNAL_KEYWORDS = [
    "how much", "what was", "what is", "what are",
    "compare", "comparison", "vs", "versus",
    "growth", "change", "increase", "decrease", "decline",
    "yoy", "year-over-year", "year over year",
    "qoq", "quarter-over-quarter", "quarter over quarter",
    "margin", "ratio", "percentage", "percent",
]

# Narrative override keywords that force NARRATIVE route even if a concept keyword is present
NARRATIVE_OVERRIDE_KEYWORDS = [
    "risk", "risks", "why", "discuss", "explain", "outlook", "concern",
    "concerns", "impact of", "factor", "factors", "strategy", "strategies",
    "challenge", "challenges", "trend", "trends", "description", "describe",
    "qualitative", "summary", "summarize", "overview"
]

# Regex patterns
_TICKER_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in KNOWN_TICKERS) + r")\b",
    re.IGNORECASE,
)
_FISCAL_YEAR_PATTERN = re.compile(r"\b(20\d{2})\b")
_FISCAL_PERIOD_PATTERN = re.compile(r"\b(Q[1-4]|FY)\b", re.IGNORECASE)


class DeterministicRouter:
    """
    Classifies incoming financial queries into NUMERIC, NARRATIVE, CONTRADICTION, or RESTATEMENT routes
    and extracts structured metadata (ticker, concept, fiscal_year, fiscal_period) for
    direct injection into downstream engines.
    """

    def __init__(self, known_tickers: Optional[set] = None):
        self.known_tickers = known_tickers or KNOWN_TICKERS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route_query(self, query: Optional[str] = None) -> Dict[str, Any]:
        """
        Classifies and extracts structured metadata from a financial query.

        Returns a RouteResult dict:
            {
                "route_type": QueryType,
                "ticker": str | None,
                "concept": str | None,          # canonical metric key for DuckDB
                "fiscal_year": int | None,
                "fiscal_period": str | None,     # e.g. "Q1", "Q2", "FY"
                "section_filter": str | None,    # e.g. "item_7", "item_1a"
                "raw_query": str,
            }
        """
        if not query or not query.strip():
            return self._build_result(QueryType.NARRATIVE, query or "")

        query_lower = query.lower()

        # Extract structured fields
        ticker = self._extract_ticker(query)
        concept = self._extract_concept(query_lower)
        fiscal_years = self._extract_fiscal_years(query)
        fiscal_year = self._extract_fiscal_year(query)
        fiscal_period = self._extract_fiscal_period(query)
        section_filter = self._extract_section_filter(query_lower)

        # ----- Route classification (priority order) -----

        # 0. Restatement / Revision intent
        if self._has_restatement_intent(query_lower):
            route_type = QueryType.RESTATEMENT
            logger.info(
                f"Router: RESTATEMENT route for query '{query}' "
                f"(ticker={ticker}, concept={concept})"
            )
            return self._build_result(
                route_type, query,
                ticker=ticker, concept=concept,
                fiscal_year=fiscal_year, fiscal_years=fiscal_years,
                fiscal_period=fiscal_period,
                section_filter=section_filter,
            )

        # 1. Contradiction / Audit intent
        if self._has_contradiction_intent(query_lower):
            route_type = QueryType.CONTRADICTION
            logger.info(
                f"Router: CONTRADICTION route for query '{query}' "
                f"(ticker={ticker}, section={section_filter})"
            )
            return self._build_result(
                route_type, query,
                ticker=ticker, concept=concept,
                fiscal_year=fiscal_year, fiscal_years=fiscal_years,
                fiscal_period=fiscal_period,
                section_filter=section_filter,
            )

        # 2. Check for narrative override signals (e.g. "supply chain risks affecting cash flow")
        has_narrative_override = self._has_narrative_override(query_lower)

        # 3. Numeric intent classification
        has_numeric_signals = self._has_numeric_intent(query_lower)
        
        if concept and not has_narrative_override:
            if has_numeric_signals or fiscal_year or fiscal_period or fiscal_years:
                route_type = QueryType.NUMERIC
            elif len(query_lower.split()) <= 5:
                # Concise lookup query like "AAPL total assets" or "Apple revenue"
                route_type = QueryType.NUMERIC
            else:
                route_type = QueryType.NARRATIVE
        else:
            route_type = QueryType.NARRATIVE

        if route_type == QueryType.NUMERIC:
            logger.info(
                f"Router: NUMERIC route for query '{query}' "
                f"(ticker={ticker}, concept={concept}, year={fiscal_year}, period={fiscal_period})"
            )
            return self._build_result(
                route_type, query,
                ticker=ticker, concept=concept,
                fiscal_year=fiscal_year, fiscal_years=fiscal_years,
                fiscal_period=fiscal_period,
                section_filter=section_filter,
            )

        # 4. Default: Narrative hybrid search
        route_type = QueryType.NARRATIVE
        logger.info(f"Router: NARRATIVE route for query '{query}' (ticker={ticker})")
        return self._build_result(
            route_type, query,
            ticker=ticker, concept=concept,
            fiscal_year=fiscal_year, fiscal_years=fiscal_years,
            fiscal_period=fiscal_period,
            section_filter=section_filter,
        )

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def _extract_ticker(self, query: str) -> Optional[str]:
        """Extracts the first recognized ticker symbol from the query."""
        query_lower = query.lower()
        # Check company names first (e.g. "Apple" -> "AAPL")
        for comp_name, ticker_sym in COMPANY_NAME_MAP.items():
            if comp_name in query_lower:
                return ticker_sym

        match = _TICKER_PATTERN.search(query)
        if match:
            return match.group(1).upper()
        # Fallback: look for any 2-5 uppercase letter word that could be a ticker
        fallback = re.findall(r"\b([A-Z]{2,5})\b", query)
        stoplist = {
            "AND", "THE", "FOR", "NOT", "BUT", "WITH", "FROM", "WAS", "ARE", "HAS",
            "SEC", "GAAP", "EPS", "ROE", "ROIC", "EBIT", "EBITDA", "YOY", "QOQ",
            "CAGR", "USD", "FY", "CEO", "CFO", "CPA", "IRS", "ITEM", "NOTE", "PART",
            "PAGE", "YEAR", "FORM", "DATA", "TOTAL", "NET", "CASH", "COST", "DEBT",
        }
        for candidate in fallback:
            if candidate not in stoplist:
                return candidate
        return None

    def _extract_concept(self, query_lower: str) -> Optional[str]:
        """
        Maps natural-language terms to canonical metric keys.
        Returns the DuckDB-compatible concept key (e.g. 'revenue', 'net_income').
        """
        for keyword in _CONCEPT_KEYS_SORTED:
            if keyword in query_lower:
                return CONCEPT_KEYWORDS[keyword]
        return None

    def _extract_fiscal_years(self, query: str) -> List[int]:
        """Extracts all 4-digit fiscal years (2000-2099 range) from the query."""
        matches = _FISCAL_YEAR_PATTERN.findall(query)
        years: List[int] = []
        for m in matches:
            val = int(m)
            if val not in years:
                years.append(val)
        return years

    def _extract_fiscal_year(self, query: str) -> Optional[int]:
        """Extracts primary 4-digit fiscal year (defaults to latest year found in query)."""
        years = self._extract_fiscal_years(query)
        if years:
            return max(years)
        return None

    def _extract_fiscal_period(self, query: str) -> Optional[str]:
        """Extracts fiscal period (Q1, Q2, Q3, Q4, FY) from the query."""
        match = _FISCAL_PERIOD_PATTERN.search(query)
        if match:
            return match.group(1).upper()
        return None

    def _extract_section_filter(self, query_lower: str) -> Optional[str]:
        """Detects explicit section references in the query (US and Indian sections)."""
        # US SEC sections
        if "item 1a" in query_lower or "risk factor" in query_lower:
            return "item_1a"
        if "item 7" in query_lower or ("md&a" in query_lower and "board" not in query_lower):
            return "item_7"
        if "item 8" in query_lower or "footnote" in query_lower:
            return "item_8"
        # Indian sections
        if "management discussion" in query_lower or "mda" in query_lower:
            return "mda"
        if "board report" in query_lower or "directors report" in query_lower or "director's report" in query_lower:
            return "board_report"
        if "notes to accounts" in query_lower or "notes to financial" in query_lower:
            return "notes"
        if "auditor report" in query_lower or "audit report" in query_lower or "auditor's report" in query_lower:
            return "auditor_report"
        return None

    def _has_restatement_intent(self, query_lower: str) -> bool:
        """Checks if the query signals a restatement/revision audit need."""
        return any(kw in query_lower for kw in RESTATEMENT_KEYWORDS)

    def _has_contradiction_intent(self, query_lower: str) -> bool:
        """Checks if the query signals a contradiction/audit verification need."""
        return any(kw in query_lower for kw in CONTRADICTION_KEYWORDS)

    def _has_numeric_intent(self, query_lower: str) -> bool:
        """Checks if the query signals a numeric lookup or comparison need."""
        return any(kw in query_lower for kw in NUMERIC_SIGNAL_KEYWORDS)

    def _has_narrative_override(self, query_lower: str) -> bool:
        """Checks if the query contains explicit narrative intent keywords (e.g. risk, explain, outlook)."""
        return any(kw in query_lower for kw in NARRATIVE_OVERRIDE_KEYWORDS)


    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_result(
        route_type: QueryType,
        raw_query: str,
        ticker: Optional[str] = None,
        concept: Optional[str] = None,
        fiscal_year: Optional[int] = None,
        fiscal_years: Optional[List[int]] = None,
        fiscal_period: Optional[str] = None,
        section_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Auto-detect market from ticker
        market = "US"
        if ticker:
            from src.ingestion.market_router import detect_market
            market = detect_market(ticker)

        return {
            "route_type": route_type,
            "ticker": ticker,
            "concept": concept,
            "fiscal_year": fiscal_year,
            "fiscal_years": fiscal_years or ([fiscal_year] if fiscal_year else []),
            "fiscal_period": fiscal_period,
            "section_filter": section_filter,
            "raw_query": raw_query,
            "market": market,
        }
