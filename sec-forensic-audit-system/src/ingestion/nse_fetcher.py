"""
NSE Fetcher: Ingests financial data for Indian NSE/BSE listed companies via yfinance.
Fetches income statements, balance sheets, and cash flow statements,
then normalizes them into flat fact records compatible with the DuckDB schema.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

try:
    import yfinance as yf
except ImportError:
    yf = None

import pandas as pd

from src.config import INDIAN_DATA_DIR, NSE_SUFFIX, BSE_SUFFIX

logger = logging.getLogger(__name__)


class NSEFetcher:
    """
    Handles fetching and caching financial data for Indian NSE/BSE listed companies
    using the yfinance library (Yahoo Finance API).
    """

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = Path(output_dir) if output_dir else INDIAN_DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _normalize_ticker(self, ticker: str) -> str:
        """Ensures ticker has .NS or .BO suffix; defaults to .NS (NSE)."""
        ticker = ticker.strip().upper()
        if not ticker.endswith(NSE_SUFFIX.upper()) and not ticker.endswith(BSE_SUFFIX.upper()):
            ticker = f"{ticker}{NSE_SUFFIX}"
        return ticker

    def _get_base_ticker(self, ticker: str) -> str:
        """Returns the base ticker without exchange suffix (e.g. RELIANCE.NS → RELIANCE)."""
        return ticker.replace(NSE_SUFFIX, "").replace(BSE_SUFFIX, "").replace(".ns", "").replace(".bo", "").upper()

    def _get_ticker_dir(self, ticker: str) -> Path:
        base = self._get_base_ticker(ticker)
        ticker_dir = self.output_dir / base
        ticker_dir.mkdir(parents=True, exist_ok=True)
        return ticker_dir

    def fetch_company_facts(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches financial statements for an Indian company via yfinance and
        normalizes them into flat fact records compatible with DuckDB ingestion.
        Caches results as JSON.
        """
        ticker = self._normalize_ticker(ticker)
        base_ticker = self._get_base_ticker(ticker)
        ticker_dir = self._get_ticker_dir(ticker)
        facts_file = ticker_dir / "financial_facts.json"

        # Return cached copy if available
        if facts_file.exists():
            logger.info(f"Loading cached financial facts for {ticker} from {facts_file}")
            with open(facts_file, "r", encoding="utf-8") as f:
                return json.load(f)

        logger.info(f"Fetching financial data from Yahoo Finance for ticker: {ticker}")
        if yf is None:
            raise ImportError("The 'yfinance' package is required for Indian market data. Install it with: pip install yfinance")
        stock = yf.Ticker(ticker)

        # Fetch company info
        try:
            info = stock.info or {}
        except Exception as e:
            logger.warning(f"Could not fetch company info for {ticker}: {e}")
            info = {}

        company_name = info.get("longName") or info.get("shortName") or base_ticker

        # Fetch all financial statements
        all_facts: List[Dict[str, Any]] = []

        # Annual Income Statement
        all_facts.extend(self._extract_facts_from_df(
            stock.income_stmt, ticker, base_ticker, "annual", "income"
        ))
        # Quarterly Income Statement
        all_facts.extend(self._extract_facts_from_df(
            stock.quarterly_income_stmt, ticker, base_ticker, "quarterly", "income"
        ))
        # Annual Balance Sheet
        all_facts.extend(self._extract_facts_from_df(
            stock.balance_sheet, ticker, base_ticker, "annual", "balance"
        ))
        # Quarterly Balance Sheet
        all_facts.extend(self._extract_facts_from_df(
            stock.quarterly_balance_sheet, ticker, base_ticker, "quarterly", "balance"
        ))
        # Annual Cash Flow
        all_facts.extend(self._extract_facts_from_df(
            stock.cashflow, ticker, base_ticker, "annual", "cashflow"
        ))
        # Quarterly Cash Flow
        all_facts.extend(self._extract_facts_from_df(
            stock.quarterly_cashflow, ticker, base_ticker, "quarterly", "cashflow"
        ))

        facts_data: Dict[str, Any] = {
            "ticker": ticker,
            "base_ticker": base_ticker,
            "name": company_name,
            "market": "INDIA",
            "currency": info.get("financialCurrency", "INR"),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "market_cap": info.get("marketCap", 0),
            "facts": all_facts,
        }

        # Cache to disk
        with open(facts_file, "w", encoding="utf-8") as f:
            json.dump(facts_data, f, indent=2, default=str)

        logger.info(f"Saved {len(all_facts)} financial facts for {ticker} ({company_name}) to {facts_file}")
        return facts_data

    def _extract_facts_from_df(
        self,
        df: Optional[pd.DataFrame],
        ticker: str,
        base_ticker: str,
        frequency: str,  # "annual" or "quarterly"
        statement_type: str,  # "income", "balance", "cashflow"
    ) -> List[Dict[str, Any]]:
        """
        Converts a yfinance financial statement DataFrame into flat fact records.
        Columns in yfinance DataFrames are dates (period end), rows are financial concepts.
        """
        if df is None or df.empty:
            return []

        facts: List[Dict[str, Any]] = []

        for concept_label in df.index:
            for col_date in df.columns:
                val = df.loc[concept_label, col_date]

                # Skip NaN/None values
                if pd.isna(val):
                    continue

                try:
                    numeric_val = float(val)
                except (ValueError, TypeError):
                    continue

                # Determine fiscal year and period from column date
                if hasattr(col_date, "year"):
                    fiscal_year = col_date.year
                    period_end = str(col_date.date()) if hasattr(col_date, "date") else str(col_date)
                    # Indian fiscal year ends March 31; if date is Jan-Mar, fiscal year is same calendar year
                    if hasattr(col_date, "month"):
                        month = col_date.month
                        if frequency == "quarterly":
                            # Map to quarters: Apr-Jun=Q1, Jul-Sep=Q2, Oct-Dec=Q3, Jan-Mar=Q4
                            if month in (4, 5, 6):
                                fiscal_period = "Q1"
                            elif month in (7, 8, 9):
                                fiscal_period = "Q2"
                            elif month in (10, 11, 12):
                                fiscal_period = "Q3"
                            else:
                                fiscal_period = "Q4"
                        else:
                            fiscal_period = "FY"
                    else:
                        fiscal_period = "FY" if frequency == "annual" else "Q"
                else:
                    fiscal_year = None
                    period_end = str(col_date)
                    fiscal_period = "FY" if frequency == "annual" else "Q"

                # Determine form type
                form = "annual" if frequency == "annual" else "quarterly"

                facts.append({
                    "ticker": ticker,
                    "form": form,
                    "fiscal_year": fiscal_year,
                    "fiscal_period": fiscal_period,
                    "concept": str(concept_label),
                    "label": str(concept_label),
                    "val": numeric_val,
                    "numeric_value": numeric_val,
                    "value": numeric_val,
                    "unit": "INR",
                    "period_type": "instant" if statement_type == "balance" else "duration",
                    "period_start": "",
                    "period_end": period_end,
                    "filed_date": period_end,
                    "accession_number": "",
                    "statement_type": statement_type,
                    "market": "INDIA",
                })

        logger.info(
            f"Extracted {len(facts)} {frequency} {statement_type} facts for {base_ticker}"
        )
        return facts

    def ingest_to_duckdb(self, ticker: str, db_engine: Any) -> bool:
        """
        Fetches company facts via yfinance and ingests them into DuckDB using db_engine.
        Returns True if facts were successfully fetched and stored, False otherwise.
        """
        try:
            facts_data = self.fetch_company_facts(ticker)
            if not facts_data or not facts_data.get("facts"):
                logger.warning(f"No facts retrieved for ticker {ticker}")
                return False
            count = db_engine.ingest_facts(ticker, facts_data)
            logger.info(f"Ingested {count} facts for {ticker} into DuckDB")
            return count > 0
        except Exception as e:
            logger.error(f"Failed to ingest {ticker} to DuckDB: {e}", exc_info=True)
            return False

    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        """Fetches basic company information (sector, industry, market cap, etc.)."""
        ticker = self._normalize_ticker(ticker)
        try:
            if yf is None:
                raise ImportError("The 'yfinance' package is required for Indian market data. Install it with: pip install yfinance")
            stock = yf.Ticker(ticker)
            info = stock.info or {}
            return {
                "ticker": ticker,
                "name": info.get("longName") or info.get("shortName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", 0),
                "currency": info.get("financialCurrency", "INR"),
                "exchange": info.get("exchange", "NSE"),
                "website": info.get("website", ""),
            }
        except Exception as e:
            logger.warning(f"Could not fetch company info for {ticker}: {e}")
            return {"ticker": ticker, "name": "", "error": str(e)}


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Fetch Indian NSE/BSE financial data via yfinance")
    parser.add_argument("--ticker", type=str, default="RELIANCE.NS", help="NSE/BSE ticker (e.g. RELIANCE.NS, TCS.NS)")
    args = parser.parse_args()

    fetcher = NSEFetcher()
    facts = fetcher.fetch_company_facts(args.ticker)
    print(f"Successfully fetched {len(facts.get('facts', []))} financial facts for {args.ticker} ({facts.get('name')})")
