"""
EDGAR Fetcher: Ingests machine-readable XBRL JSON facts and raw HTML filings via edgartools.
"""
import sys

# Fix: truststore v0.10.4 on Python 3.11 causes SSLContext.verify_mode recursion (~500 deep).
# Increasing the limit prevents RecursionError during SEC EDGAR HTTPS handshakes.
sys.setrecursionlimit(10000)

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Ensure base project path is in sys.path when executed directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from edgar import set_identity, Company  # type: ignore[import-untyped]
from src.config import SEC_EDGAR_IDENTITY, DATA_DIR

logger = logging.getLogger(__name__)


class EdgarFetcher:
    """
    Handles fetching and caching SEC filings (10-K / 10-Q) and XBRL facts
    for any specified company ticker.
    """

    def __init__(self, output_dir: Optional[Path] = None, identity: Optional[str] = None):
        self.output_dir = Path(output_dir) if output_dir else DATA_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Register SEC Identity Header
        sec_identity = identity or SEC_EDGAR_IDENTITY
        set_identity(sec_identity)

    def _get_ticker_dir(self, ticker: str) -> Path:
        ticker_dir = self.output_dir / ticker.upper()
        ticker_dir.mkdir(parents=True, exist_ok=True)
        return ticker_dir

    def fetch_company_facts(self, ticker: str) -> Dict[str, Any]:
        """
        Fetches machine-readable XBRL facts for a ticker and caches them as JSON.
        """
        ticker = ticker.upper()
        ticker_dir = self._get_ticker_dir(ticker)
        facts_file = ticker_dir / "xbrl_facts.json"

        # Return cached copy if available
        if facts_file.exists():
            logger.info(f"Loading cached XBRL facts for {ticker} from {facts_file}")
            with open(facts_file, "r", encoding="utf-8") as f:
                return json.load(f)

        logger.info(f"Fetching XBRL facts from SEC EDGAR for ticker: {ticker}")
        company = Company(ticker)
        facts_obj = company.get_facts()

        facts_data: Dict[str, Any] = {
            "ticker": ticker,
            "cik": company.cik,
            "name": company.name,
        }

        if facts_obj is None:
            logger.warning(f"No XBRL facts returned for {ticker}")
            facts_data["facts"] = []
        elif hasattr(facts_obj, "to_dataframe"):
            # Preferred: convert EntityFacts to a pandas DataFrame then to records
            df = facts_obj.to_dataframe()
            facts_data["facts"] = df.to_dict(orient="records")
        elif hasattr(facts_obj, "get_all_facts"):
            # Fallback: get_all_facts() returns a list of FinancialFact objects
            all_facts = facts_obj.get_all_facts()
            facts_data["facts"] = [
                vars(item) if hasattr(item, "__dict__") else str(item)
                for item in all_facts
            ]
        else:
            facts_data["facts"] = str(facts_obj)

        with open(facts_file, "w", encoding="utf-8") as f:
            json.dump(facts_data, f, indent=2, default=str)

        logger.info(f"Saved XBRL facts for {ticker} to {facts_file}")
        return facts_data

    def fetch_filing_html(self, ticker: str, form_type: str = "10-K", year: Optional[int] = None) -> str:
        """
        Fetches raw HTML filing document for a ticker, form type (10-K/10-Q), and optional year.
        Caches filing HTML to disk.
        """
        ticker = ticker.upper()
        ticker_dir = self._get_ticker_dir(ticker)
        filings_dir = ticker_dir / "filings"
        filings_dir.mkdir(parents=True, exist_ok=True)

        year_suffix = f"_{year}" if year else "_latest"
        html_file = filings_dir / f"{form_type}{year_suffix}.html"

        # Return cached HTML if available
        if html_file.exists():
            logger.info(f"Loading cached {form_type} HTML for {ticker} from {html_file}")
            with open(html_file, "r", encoding="utf-8") as f:
                return f.read()

        logger.info(f"Fetching {form_type} filing HTML from SEC EDGAR for {ticker}...")
        company = Company(ticker)
        filings = company.get_filings(form=form_type)

        if not filings:
            raise ValueError(f"No filings found of type '{form_type}' for ticker '{ticker}'")

        selected_filing = None
        for filing in filings:
            # Prioritize exact form match (e.g., "10-K" over "10-K/A")
            if getattr(filing, "form", "") == form_type:
                selected_filing = filing
                break

        if selected_filing is None and len(filings) > 0:
            selected_filing = filings[0]  # fallback to first filing if exact form match not found

        if year and selected_filing:
            for filing in filings:
                if str(year) in str(getattr(filing, "filing_date", "")) and getattr(filing, "form", "") == form_type:
                    selected_filing = filing
                    break


        html_content: str = selected_filing.html() or ""  # type: ignore[union-attr]
        if not html_content:
            html_content = selected_filing.text() or ""  # type: ignore[union-attr]

        if not html_content:
            raise ValueError(f"No HTML or text content found for {form_type} filing of '{ticker}'")

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"Saved {form_type} HTML for {ticker} to {html_file}")
        return html_content


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description="Fetch SEC XBRL facts & HTML filings")
    parser.add_argument("--ticker", type=str, default="AAPL", help="Company ticker symbol (e.g. AAPL, NVDA)")
    parser.add_argument("--form", type=str, default="10-K", help="Filing form type (10-K or 10-Q)")
    parser.add_argument("--year", type=int, default=None, help="Filing year (optional)")
    args = parser.parse_args()

    fetcher = EdgarFetcher()
    facts = fetcher.fetch_company_facts(args.ticker)
    print(f"Successfully fetched {len(facts.get('facts', []))} XBRL facts for {args.ticker} ({facts.get('name')})")

    html = fetcher.fetch_filing_html(args.ticker, form_type=args.form, year=args.year)
    print(f"Successfully fetched {args.form} HTML filing ({len(html)} bytes)")
