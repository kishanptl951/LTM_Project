"""
Launcher wrapper: applies truststore SSL fix before any imports to prevent
the infinite recursion stack overflow bug on Python 3.11 + truststore 0.10.4.
"""
import sys
import os

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Apply SSL fix BEFORE any HTTPS-related imports
from src.ssl_fix import apply_truststore_ssl_fix  # noqa: E402

# Now run the pipeline
from src.pipeline import run_pipeline  # noqa: E402
from src.config import DEFAULT_TICKER, DEFAULT_FORM_TYPE  # noqa: E402

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SEC Forensic Audit Pipeline")
    parser.add_argument("--ticker", type=str, default=DEFAULT_TICKER, help="Company ticker symbol")
    parser.add_argument("--form", type=str, default=DEFAULT_FORM_TYPE, help="Filing form type")
    parser.add_argument("--year", type=int, default=None, help="Filing year (optional)")
    args = parser.parse_args()
    run_pipeline(ticker=args.ticker, form_type=args.form, year=args.year)
