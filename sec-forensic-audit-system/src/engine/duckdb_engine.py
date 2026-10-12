"""
DuckDB Financial Metric Engine:
Executes direct SQL queries over structured financial facts (US-GAAP & Ind-AS) for 100% precision
with 0 hallucinations. Supports dual-market (US + India) with market-aware concept mapping.
Includes duration vs instant period tracking, source accession numbers, and metric concept mapping.
"""
import os
import logging
from pathlib import Path
import duckdb
import pandas as pd
from typing import Dict, Any, List, Optional, Union, Tuple, cast

from src.config import DUCKDB_PATH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# US-GAAP Concept Mappings (for US Market / SEC EDGAR tickers)
# ---------------------------------------------------------------------------
US_GAAP_METRIC_MAP: Dict[str, List[str]] = {
    "revenue": [
        "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
        "us-gaap:SalesRevenueNet",
        "us-gaap:Revenues",
        "us-gaap:InterestAndDividendIncomeOperating",
        "us-gaap:revenue",
        "revenue",
    ],
    "net_income": [
        "us-gaap:NetIncomeLoss",
        "us-gaap:ProfitLoss",
        "us-gaap:net_income",
        "net_income",
    ],
    "gross_profit": [
        "us-gaap:GrossProfit",
        "us-gaap:gross_profit",
        "gross_profit",
    ],
    "operating_income": [
        "us-gaap:OperatingIncomeLoss",
        "us-gaap:operating_income",
        "operating_income",
    ],
    "total_assets": [
        "us-gaap:Assets",
        "us-gaap:total_assets",
        "total_assets",
    ],
    "total_liabilities": [
        "us-gaap:Liabilities",
        "us-gaap:total_liabilities",
        "total_liabilities",
    ],
    "cash": [
        "us-gaap:CashAndCashEquivalentsAtCarryingValue",
        "us-gaap:cash",
        "cash",
    ],
    "operating_cash_flow": [
        "us-gaap:NetCashProvidedByUsedInOperatingActivities",
        "us-gaap:operating_cash_flow",
        "operating_cash_flow",
    ],
    "capital_expenditure": [
        "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment",
        "us-gaap:PaymentsToAcquireProductiveAssets",
        "capital_expenditure",
    ],
    "rnd_expense": [
        "us-gaap:ResearchAndDevelopmentExpense",
        "rnd_expense",
    ],
    "operating_expenses": [
        "us-gaap:OperatingExpenses",
        "operating_expenses",
    ],
}

# ---------------------------------------------------------------------------
# Ind-AS / yfinance Concept Mappings (for Indian Market / NSE/BSE tickers)
# ---------------------------------------------------------------------------
INDIAN_METRIC_MAP: Dict[str, List[str]] = {
    "revenue": [
        "Total Revenue", "Revenue From Operations", "Operating Revenue",
        "Net Revenue", "Total Operating Revenues",
    ],
    "net_income": [
        "Net Income", "Net Income From Continuing Operations",
        "Profit For The Period", "Net Income Common Stockholders",
        "Net Income Including Noncontrolling Interests",
    ],
    "gross_profit": [
        "Gross Profit",
    ],
    "operating_income": [
        "Operating Income", "EBIT", "Operating Profit",
    ],
    "total_assets": [
        "Total Assets",
    ],
    "total_liabilities": [
        "Total Liabilities Net Minority Interest", "Total Debt",
        "Total Non Current Liabilities Net Minority Interest",
    ],
    "cash": [
        "Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments",
        "Cash Financial", "Cash Equivalents",
    ],
    "operating_cash_flow": [
        "Operating Cash Flow", "Cash Flow From Continuing Operating Activities",
        "Changes In Cash",
    ],
    "capital_expenditure": [
        "Capital Expenditure", "Purchase Of PPE",
        "Net PPE Purchase And Sale",
    ],
    "depreciation": [
        "Depreciation And Amortization", "Depreciation Amortization Depletion",
        "Depreciation",
    ],
    "tax_expense": [
        "Tax Provision", "Income Tax Expense", "Tax Effect Of Unusual Items",
    ],
    "interest_expense": [
        "Interest Expense", "Interest Expense Non Operating",
        "Net Interest Income",
    ],
    "ebitda": [
        "EBITDA", "Normalized EBITDA", "Reconciled Depreciation",
    ],
    "operating_expenses": [
        "Operating Expense", "Total Expenses",
        "Selling General And Administration",
    ],
}

# Unified map: merges both for backward compatibility
STANDARD_METRIC_MAP: Dict[str, List[str]] = {}
for key in set(list(US_GAAP_METRIC_MAP.keys()) + list(INDIAN_METRIC_MAP.keys())):
    STANDARD_METRIC_MAP[key] = (
        US_GAAP_METRIC_MAP.get(key, []) + INDIAN_METRIC_MAP.get(key, [])
    )


def get_metric_map_for_market(market: str) -> Dict[str, List[str]]:
    """Returns the appropriate metric concept map for the given market."""
    if market == "INDIA":
        return INDIAN_METRIC_MAP
    return US_GAAP_METRIC_MAP


class FinancialMetricEngine:
    """
    Handles persisting XBRL financial facts into embedded DuckDB storage
    and executing deterministic SQL metric queries.
    """

    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = str(db_path) if db_path else str(DUCKDB_PATH)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Retry connection to handle single-writer file lock during parallel pipeline runs
        import time
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.conn = duckdb.connect(self.db_path)
                break
            except duckdb.IOException as e:
                try:
                    self.conn = duckdb.connect(self.db_path, read_only=True)
                    logger.info("Connected to DuckDB in read-only mode (file locked by another process).")
                    break
                except Exception:
                    pass
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"DuckDB file locked by another process. Retrying in 2 seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(2)
                
        try:
            self._init_schema()
        except duckdb.InvalidInputException:
            logger.info("Skipped schema initialization on read-only connection.")
        except Exception as e:
            if "read-only" in str(e).lower() or "read_only" in str(e).lower():
                logger.info("Skipped schema initialization on read-only connection.")
            else:
                raise e

    def _init_schema(self) -> None:
        """Initializes financial_facts table schema and index, supporting schema migration."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS financial_facts (
                ticker VARCHAR,
                form VARCHAR,
                fiscal_year INT,
                fiscal_period VARCHAR,
                concept VARCHAR,
                label VARCHAR,
                val DOUBLE,
                unit VARCHAR,
                filed_date VARCHAR,
                period_type VARCHAR,
                period_start VARCHAR,
                period_end VARCHAR,
                accession_number VARCHAR,
                market VARCHAR,
                statement_type VARCHAR
            )
        """)

        # Schema migration check: ensure all columns exist if table was created under older schema
        existing_cols = set(self.conn.execute("DESCRIBE financial_facts").df()["column_name"].tolist())
        required_cols = {
            "period_type": "VARCHAR",
            "period_start": "VARCHAR",
            "period_end": "VARCHAR",
            "accession_number": "VARCHAR",
            "market": "VARCHAR",
            "statement_type": "VARCHAR",
        }
        for col_name, col_type in required_cols.items():
            if col_name not in existing_cols:
                self.conn.execute(f"ALTER TABLE financial_facts ADD COLUMN {col_name} {col_type}")

        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_facts_lookup 
            ON financial_facts (ticker, concept, fiscal_year, fiscal_period)
        """)

    def ingest_facts(self, ticker: str, facts_data: Dict[str, Any]) -> int:
        """
        Parses raw XBRL facts dictionary/list and stores them into the DuckDB financial_facts table.
        Replaces previous records for the ticker to prevent duplicate entries on re-ingestion.
        Returns the number of ingested fact rows.
        """
        ticker = ticker.upper()
        raw_facts = facts_data.get("facts", [])

        if not raw_facts or not isinstance(raw_facts, list):
            logger.warning(f"No valid fact list found in facts_data for {ticker}")
            return 0

        parsed_rows: List[Dict[str, Any]] = []
        skipped_non_numeric = 0
        fallback_filed_date_count = 0

        for fact in raw_facts:
            if not isinstance(fact, dict):
                continue

            # Extract numeric value safely
            val = fact.get("numeric_value")
            if val is None:
                val = fact.get("value")
            if val is None:
                val = fact.get("val")

            try:
                numeric_val = float(val) if val is not None else None
            except (ValueError, TypeError):
                numeric_val = None

            if numeric_val is None:
                skipped_non_numeric += 1
                continue

            concept = str(fact.get("concept", ""))
            label = str(fact.get("label", ""))
            unit = str(fact.get("unit", "USD"))
            fiscal_period = str(fact.get("fiscal_period", "FY")).upper()
            
            # Form type heuristic
            form = str(fact.get("form") or fact.get("form_type") or ("10-K" if fiscal_period == "FY" else "10-Q"))
            
            # Fiscal year extraction
            fy_raw = fact.get("fiscal_year")
            try:
                fiscal_year = int(fy_raw) if fy_raw is not None else None
            except (ValueError, TypeError):
                fiscal_year = None

            # Duration vs Instant dates & source tracing
            period_type = str(fact.get("period_type", "duration"))
            period_start = str(fact.get("period_start") or "")
            period_end = str(fact.get("period_end") or "")

            raw_filed_date = fact.get("filed_date")
            if raw_filed_date:
                filed_date = str(raw_filed_date)
            else:
                filed_date = period_end
                fallback_filed_date_count += 1

            accession_number = str(fact.get("accession_number") or fact.get("accession") or "")

            market = str(fact.get("market", "US"))
            statement_type = str(fact.get("statement_type", ""))

            parsed_rows.append({
                "ticker": ticker,
                "form": form,
                "fiscal_year": fiscal_year,
                "fiscal_period": fiscal_period,
                "concept": concept,
                "label": label,
                "val": numeric_val,
                "unit": unit,
                "period_type": period_type,
                "period_start": period_start,
                "period_end": period_end,
                "filed_date": filed_date,
                "accession_number": accession_number,
                "market": market,
                "statement_type": statement_type,
            })

        if not parsed_rows:
            logger.warning(f"No numeric facts parsed for {ticker} (skipped {skipped_non_numeric} non-numeric entries)")
            return 0

        df = pd.DataFrame(parsed_rows)

        # Explicitly cast column data types to prevent DuckDB string/object conversion notices
        string_cols = ["ticker", "form", "fiscal_period", "concept", "label", "unit", "period_type", "period_start", "period_end", "filed_date", "accession_number", "market", "statement_type"]
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        if "val" in df.columns:
            df["val"] = pd.to_numeric(df["val"], errors="coerce")

        # Deduplicate intra-batch duplicate facts (same concept reported twice under dimensions)
        df = df.drop_duplicates(
            subset=["ticker", "fiscal_year", "fiscal_period", "concept", "period_start", "period_end", "accession_number"],
            keep="first"
        )


        # Atomic transaction & robust temp table unregistration
        self.conn.register("temp_facts_df", df)
        try:
            self.conn.execute("DROP INDEX IF EXISTS idx_facts_lookup")
            
            self.conn.execute("BEGIN TRANSACTION")
            self.conn.execute("DELETE FROM financial_facts WHERE ticker = ?", [ticker])
            self.conn.execute("""
                INSERT INTO financial_facts (
                    ticker, form, fiscal_year, fiscal_period, concept, label, val, unit, 
                    period_type, period_start, period_end, filed_date, accession_number,
                    market, statement_type
                )
                SELECT ticker, form, fiscal_year, fiscal_period, concept, label, val, unit, 
                       period_type, period_start, period_end, filed_date, accession_number,
                       market, statement_type
                FROM temp_facts_df
            """)
            self.conn.execute("COMMIT")
            
            self.conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_facts_lookup 
                ON financial_facts (ticker, concept, fiscal_year, fiscal_period)
            """)
        except Exception as e:
            self.conn.execute("ROLLBACK")
            logger.error(f"Error during DuckDB ingestion for {ticker}: {e}")
            raise e
        finally:
            try:
                self.conn.unregister("temp_facts_df")
            except Exception:
                pass

        if fallback_filed_date_count > 0:
            logger.debug(f"{ticker}: {fallback_filed_date_count} facts used period_end fallback for filed_date")

        logger.info(
            f"Successfully ingested {len(df)} financial facts into DuckDB for {ticker} "
            f"(skipped {skipped_non_numeric} non-numeric facts)"
        )
        return len(df)

    def query_metric(
        self,
        ticker: str,
        concept: str,
        year: Optional[int] = None,
        period: Optional[str] = None,
        latest_only: bool = True,
        market: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Queries financial facts table using precision SQL.
        Automatically selects the correct concept map (US-GAAP or Ind-AS) based on market.
        Concept search supports:
        - Exact concept tags (e.g. 'us-gaap:RevenueFromContractWithCustomer...' or 'Total Revenue')
        - Standard metric keys ('revenue', 'net_income', 'gross_profit', 'operating_income', 'total_assets')
        - Fuzzy keyword matches (e.g. 'Revenue')
        """
        ticker = ticker.upper()
        concept_lower = concept.lower()

        # Auto-detect market from ticker if not provided
        if market is None:
            from src.ingestion.market_router import detect_market
            market = detect_market(ticker)

        # Select appropriate concept map
        active_metric_map = get_metric_map_for_market(market)

        query = """
            SELECT ticker, form, fiscal_year, fiscal_period, concept, label, val, unit, 
                   period_type, period_start, period_end, filed_date, accession_number,
                   market, statement_type
            FROM financial_facts
            WHERE ticker = ?
        """
        params: List[Any] = [ticker]

        # Concept search resolution
        if ":" in concept or concept.startswith("dei:"):
            query += " AND concept = ?"
            params.append(concept)
        elif concept_lower in active_metric_map:
            mapped_concepts = active_metric_map[concept_lower]
            placeholders = ", ".join(["?"] * len(mapped_concepts))
            query += f" AND concept IN ({placeholders})"
            params.extend(mapped_concepts)
        elif concept_lower in STANDARD_METRIC_MAP:
            # Fallback to unified map if not in market-specific map
            mapped_concepts = STANDARD_METRIC_MAP[concept_lower]
            placeholders = ", ".join(["?"] * len(mapped_concepts))
            query += f" AND concept IN ({placeholders})"
            params.extend(mapped_concepts)
        else:
            query += " AND (concept ILIKE ? OR label ILIKE ?)"
            pattern = f"%{concept}%"
            params.extend([pattern, pattern])

        if year is not None:
            query += " AND fiscal_year = ?"
            params.append(year)

        if period is not None:
            query += " AND fiscal_period = ?"
            params.append(period.upper())

        query += " ORDER BY fiscal_year DESC, filed_date DESC, accession_number DESC"

        logger.info(f"Executing DuckDB SQL query for {ticker} (concept='{concept}', year={year}, period={period})")
        df = self.conn.execute(query, params).df()

        if latest_only and not df.empty:
            # Deduplicate multiple restated filings by prioritizing latest filed_date per (fiscal_year, fiscal_period, concept)
            df = df.drop_duplicates(subset=["fiscal_year", "fiscal_period", "concept"], keep="first")

        return df

    def detect_restatements(
        self,
        ticker: str,
        concept: Optional[str] = None,
        year: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Detects accounting restatements and figure revisions across filings.
        Finds instances where a metric for a specific period (fiscal_year, fiscal_period, concept)
        was reported with differing values across filings.
        """
        ticker = ticker.upper()
        search_concept = concept or "revenue"
        
        # Get all records without deduplication
        raw_df = self.query_metric(ticker=ticker, concept=search_concept, year=year, latest_only=False)
        if raw_df.empty:
            return pd.DataFrame()

        # Group by fiscal_year, fiscal_period, period_start, period_end, concept to find value discrepancies
        grouped = raw_df.groupby(["fiscal_year", "fiscal_period", "period_start", "period_end", "concept"])
        
        restated_records: List[Dict[str, Any]] = []
        for key, group in grouped:
            fy, fp, p_start, p_end, conc = cast(Tuple[Any, Any, Any, Any, Any], key)
            unique_vals = group["val"].nunique()
            if unique_vals > 1:
                # Sort group chronologically / by entry order
                sorted_group = group.sort_values(by=["filed_date", "val"], ascending=[True, True])
                first_row = sorted_group.iloc[0]
                last_row = sorted_group.iloc[-1]
                
                orig_val = float(first_row["val"])
                latest_val = float(last_row["val"])
                diff = latest_val - orig_val
                pct_change = (diff / abs(orig_val) * 100.0) if orig_val != 0 else 0.0
                
                restated_records.append({
                    "ticker": ticker,
                    "fiscal_year": fy,
                    "fiscal_period": fp,
                    "concept": conc,
                    "label": str(first_row.get("label") or conc),
                    "original_val": orig_val,
                    "latest_val": latest_val,
                    "variance_usd": diff,
                    "variance_pct": pct_change,
                    "revision_count": len(group),
                    "distinct_values_count": unique_vals,
                })
                
        if not restated_records:
            return pd.DataFrame()
            
        res_df = pd.DataFrame(restated_records)
        return res_df.sort_values(by=["fiscal_year", "variance_usd"], ascending=[False, False])


    def get_available_concepts(self, ticker: str, filter_term: Optional[str] = None) -> List[str]:
        """Returns distinct concept tags stored in DuckDB for a ticker."""
        ticker = ticker.upper()
        query = "SELECT DISTINCT concept FROM financial_facts WHERE ticker = ?"
        params: List[Any] = [ticker]

        if filter_term:
            query += " AND (concept ILIKE ? OR label ILIKE ?)"
            pattern = f"%{filter_term}%"
            params.extend([pattern, pattern])

        query += " ORDER BY concept ASC"
        df = self.conn.execute(query, params).df()
        return df["concept"].tolist() if not df.empty else []

    def close(self) -> None:
        """Closes the DuckDB connection."""
        self.conn.close()
