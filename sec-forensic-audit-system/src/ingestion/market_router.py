"""
Market Router: Utility module for detecting market (US vs India) from ticker symbols
and routing to the appropriate data fetcher.
"""
import logging
from typing import Optional

from src.config import (
    MARKET_US, MARKET_INDIA,
    NSE_SUFFIX, BSE_SUFFIX,
)

logger = logging.getLogger(__name__)

# Known Indian exchange suffixes
_INDIAN_SUFFIXES = (NSE_SUFFIX, BSE_SUFFIX)

# Known US tickers (expandable — these are recognized without suffix)
KNOWN_US_TICKERS = {
    "AAPL", "TSLA", "RMD", "JPM", "NVDA", "MSFT", "GOOG", "AMZN", "META",
    "PFE", "BA", "INTC", "AMD", "WMT", "DIS", "NFLX", "GOOGL", "PYPL",
    "CRM", "ORCL", "CSCO", "ADBE", "QCOM", "TXN", "COST", "NKE", "UNH",
}

# Known Indian tickers (without suffix — for fallback detection)
KNOWN_INDIAN_TICKERS = {
    "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "WIPRO",
    "BHARTIARTL", "ITC", "HINDUNILVR", "KOTAKBANK", "ADANIENT", "BAJFINANCE",
    "MARUTI", "ASIANPAINT", "TITAN", "LT", "SUNPHARMA", "TATAMOTORS",
    "TATASTEEL", "AXISBANK", "POWERGRID", "NTPC", "ONGC", "COALINDIA",
    "ULTRACEMCO", "TECHM", "HCLTECH", "DRREDDY", "BAJAJFINSV",
    "NESTLEIND", "DIVISLAB", "CIPLA", "APOLLOHOSP", "HEROMOTOCO",
    "EICHERMOT", "GRASIM", "BRITANNIA", "JSWSTEEL", "HINDALCO",
}


def detect_market(ticker: str) -> str:
    """
    Detects which market a ticker belongs to based on suffix and known ticker lists.

    Returns:
        MARKET_US ("US") or MARKET_INDIA ("INDIA")
    """
    ticker_upper = ticker.upper().strip()

    # Check for explicit Indian exchange suffix
    if any(ticker_upper.endswith(suffix.upper()) for suffix in _INDIAN_SUFFIXES):
        return MARKET_INDIA

    # Check known Indian tickers (without suffix)
    base_ticker = ticker_upper.split(".")[0]
    if base_ticker in KNOWN_INDIAN_TICKERS:
        return MARKET_INDIA

    # Check known US tickers
    if base_ticker in KNOWN_US_TICKERS:
        return MARKET_US

    # Default: treat as US market (SEC EDGAR will validate)
    logger.info(f"Could not definitively detect market for '{ticker}', defaulting to US.")
    return MARKET_US


def normalize_ticker(ticker: str, market: Optional[str] = None) -> str:
    """
    Normalizes a ticker symbol for its target market.

    - Indian tickers: ensures .NS suffix is present (defaults to NSE)
    - US tickers: returns uppercase base ticker
    """
    ticker = ticker.strip()
    resolved_market = market or detect_market(ticker)

    if resolved_market == MARKET_INDIA:
        base = ticker.upper().replace(BSE_SUFFIX.upper(), "").replace(NSE_SUFFIX.upper(), "")
        # If user specified .BO suffix, keep it; otherwise default to .NS
        if ticker.upper().endswith(BSE_SUFFIX.upper()):
            return f"{base}{BSE_SUFFIX}"
        return f"{base}{NSE_SUFFIX}"

    # US market: plain uppercase ticker
    return ticker.upper().split(".")[0]


def get_currency_symbol(market: str) -> str:
    """Returns the currency symbol for the given market."""
    if market == MARKET_INDIA:
        return "₹"
    return "$"


def get_currency_code(market: str) -> str:
    """Returns the ISO currency code for the given market."""
    if market == MARKET_INDIA:
        return "INR"
    return "USD"


def format_indian_value(value: float) -> str:
    """
    Formats a numeric value in Indian Crore notation.
    E.g., 954230000000 → '₹9,54,230.00 Cr'
    """
    crore_val = value / 1e7
    if abs(crore_val) >= 100:
        return f"₹{crore_val:,.0f} Cr"
    elif abs(crore_val) >= 1:
        return f"₹{crore_val:,.2f} Cr"
    else:
        # Lakhs
        lakh_val = value / 1e5
        return f"₹{lakh_val:,.2f} L"


def format_value(value: float, market: str) -> str:
    """
    Formats a monetary value appropriately for its market.
    US: $254,940,000,000
    India: ₹9,54,230 Cr
    """
    if market == MARKET_INDIA:
        return format_indian_value(value)
    return f"${value:,.0f}"
