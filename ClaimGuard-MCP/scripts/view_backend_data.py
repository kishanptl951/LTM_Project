"""
ClaimGuard Backend Data Viewer
Utility script to inspect all tables and records in DuckDB (data/claimguard.duckdb).

Usage:
    python scripts/view_backend_data.py
    python scripts/view_backend_data.py --claim-id CLM-UI-001
    python scripts/view_backend_data.py --table claims
    python scripts/view_backend_data.py --export-csv
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import duckdb
from src.config import settings


def print_header(title: str, width: int = 80):
    print("\n" + "=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width)


def print_table(cursor, title: str, limit: int = 20):
    columns = [col[0] for col in cursor.description]
    rows = cursor.fetchall()

    print_header(f"{title} ({len(rows)} records shown, limit={limit})")
    if not rows:
        print("  (No records found)")
        return

    # Calculate column widths
    col_widths = {col: len(col) for col in columns}
    for row in rows:
        for col, val in zip(columns, row):
            val_str = str(val) if val is not None else "NULL"
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            col_widths[col] = max(col_widths[col], len(val_str))

    # Print header row
    header_str = " | ".join(col.ljust(col_widths[col]) for col in columns)
    sep_str = "-+-".join("-" * col_widths[col] for col in columns)
    print(header_str)
    print(sep_str)

    # Print data rows
    for row in rows:
        row_strs = []
        for col, val in zip(columns, row):
            val_str = str(val) if val is not None else "NULL"
            if len(val_str) > 40:
                val_str = val_str[:37] + "..."
            row_strs.append(val_str.ljust(col_widths[col]))
        print(" | ".join(row_strs))


def view_backend_data(table_name: str | None = None, claim_id: str | None = None, limit: int = 25, export_csv: bool = False):
    db_path = Path(settings.database_path)
    if not db_path.exists():
        print(f"❌ Database file not found at: {db_path}")
        print("Run the pipeline or Streamlit UI once to generate data.")
        return

    print(f"\n📂 Database Location: {db_path.resolve()}")
    print(f"📦 File Size: {db_path.stat().st_size / (1024 * 1024):.2f} MB")

    conn = duckdb.connect(str(db_path), read_only=True)

    # 1. Summary of all tables
    tables = [t[0] for t in conn.execute("SHOW TABLES").fetchall()]
    print("\n📊 Summary of Tables & Row Counts:")
    for t in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  • {t:<22} : {count:>5} rows")

    target_tables = [table_name] if table_name else ["claims", "documents", "policy_evaluations", "invariant_results", "extracted_evidence"]

    for tbl in target_tables:
        if tbl not in tables:
            continue

        query = f"SELECT * FROM {tbl}"
        params = []
        if claim_id:
            query += " WHERE claim_id = ?"
            params.append(claim_id)
        query += f" ORDER BY created_at DESC LIMIT {limit}"

        res = conn.execute(query, params)
        print_table(res, title=f"Table: {tbl}", limit=limit)

        if export_csv:
            export_dir = PROJECT_ROOT / "data" / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            csv_path = export_dir / f"{tbl}.csv"
            conn.execute(f"COPY ({query}) TO '{csv_path.as_posix()}' (HEADER, DELIMITER ',')")
            print(f"  💾 Exported to {csv_path}")

    conn.close()
    print("\n✅ Done.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="View ClaimGuard DuckDB backend data")
    parser.add_argument("--table", "-t", type=str, help="Specific table to view (claims, documents, extracted_evidence, policy_evaluations, invariant_results)")
    parser.add_argument("--claim-id", "-c", type=str, help="Filter records by Claim ID (e.g., CLM-UI-001)")
    parser.add_argument("--limit", "-n", type=int, default=15, help="Max rows per table (default 15)")
    parser.add_argument("--export-csv", action="store_true", help="Export queried tables to CSV in data/exports/")

    args = parser.parse_args()
    view_backend_data(table_name=args.table, claim_id=args.claim_id, limit=args.limit, export_csv=args.export_csv)
