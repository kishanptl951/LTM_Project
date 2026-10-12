"""
Configuration Module for Global Forensic Audit System (US + India).
Loads environment variables and sets system-wide constants for both markets.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

# ---------------------------------------------------------------------------
# Base Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data" / "sec_corpus"))
INDIAN_DATA_DIR = Path(os.getenv("INDIAN_DATA_DIR", BASE_DIR / "data" / "nse_corpus"))
DB_DIR = Path(os.path.dirname(os.getenv("DUCKDB_PATH", BASE_DIR / "db" / "financials.duckdb")))
DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", BASE_DIR / "db" / "financials.duckdb"))

# Ensure base directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDIAN_DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Market Constants
# ---------------------------------------------------------------------------
MARKET_US = "US"
MARKET_INDIA = "INDIA"

# ---------------------------------------------------------------------------
# US Market Configuration (SEC EDGAR)
# ---------------------------------------------------------------------------
SEC_EDGAR_IDENTITY = os.getenv("SEC_EDGAR_IDENTITY", "ForensicAuditSystem Admin@forensicaudit.com")
DEFAULT_TICKER = os.getenv("DEFAULT_TICKER", "AAPL")
DEFAULT_FORM_TYPE = os.getenv("DEFAULT_FORM_TYPE", "10-K")
US_CURRENCY = "USD"
US_CURRENCY_SYMBOL = "$"

# ---------------------------------------------------------------------------
# Indian Market Configuration (NSE / BSE via yfinance)
# ---------------------------------------------------------------------------
NSE_SUFFIX = ".NS"
BSE_SUFFIX = ".BO"
DEFAULT_INDIAN_TICKER = os.getenv("DEFAULT_INDIAN_TICKER", "RELIANCE.NS")
INDIAN_CURRENCY = "INR"
INDIAN_CURRENCY_SYMBOL = "₹"

# ---------------------------------------------------------------------------
# LLM Configuration
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_VERIFIER_ENABLED = bool(GEMINI_API_KEY.strip() and GEMINI_API_KEY != "your_gemini_api_key_here")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

