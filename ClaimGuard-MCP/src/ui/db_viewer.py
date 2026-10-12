import csv
import io
import logging
from pathlib import Path

import streamlit as st

from src.config import settings
from src.db.session import get_db_connection

logger = logging.getLogger(__name__)

ALL_TABLES = [
    "claims",
    "documents",
    "extracted_evidence",
    "policy_evaluations",
    "invariant_results",
]


def get_table_counts() -> dict[str, int]:
    """Retrieve row counts for each database table."""
    counts = {}
    try:
        with get_db_connection(read_only=True) as conn:
            existing = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
            for table in ALL_TABLES:
                if table in existing:
                    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    counts[table] = row[0] if row else 0
                else:
                    counts[table] = 0
    except Exception as exc:
        logger.error("Failed to query table counts: %s", exc)
    return counts


def render_db_explorer() -> None:
    """Render an interactive DuckDB Backend Explorer inside Streamlit."""
    st.markdown(
        """
        <div style="
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 24px; padding: 24px 28px;
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.06) 0%, rgba(139, 92, 246, 0.04) 50%, rgba(236, 72, 153, 0.04) 100%);
            border: 1px solid rgba(99, 102, 241, 0.10);
            border-radius: 22px;
            backdrop-filter: blur(12px);
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.06);
        ">
            <div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                    <span class="badge-pill badge-indigo">🗄️ Embedded Data Lake</span>
                    <span class="badge-pill badge-emerald">DuckDB OLAP</span>
                </div>
                <h1 style="
                    font-size: 2.2rem; font-weight: 800; margin: 0;
                    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 40%, #EC4899 100%);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    letter-spacing: -0.02em;
                ">
                    Backend Audit Lake Explorer
                </h1>
                <p style="margin: 6px 0 0 0; color: #64748B; font-size: 0.95rem;">
                    Query, inspect, and export persistent records, invariant verdicts, and raw multimodal evidence.
                </p>
            </div>
            <div style="text-align: right;">
                <span class="badge-pill badge-cyan">Lock-Free Read Replicas</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    db_path = Path(settings.database_path)
    file_exists = db_path.exists()
    file_size_mb = (db_path.stat().st_size / (1024 * 1024)) if file_exists else 0.0

    # ---------------------------------------------------------
    # Database Health & Summary Stats
    # ---------------------------------------------------------
    counts = get_table_counts() if file_exists else {}

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Claims", counts.get("claims", 0))
    with col2:
        st.metric("Documents", counts.get("documents", 0))
    with col3:
        st.metric("Evidence Items", counts.get("extracted_evidence", 0))
    with col4:
        st.metric("Policy Results", counts.get("policy_evaluations", 0))
    with col5:
        st.metric("Invariants Logged", counts.get("invariant_results", 0))

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    info_card = f"""
    <div style="
        background: rgba(255, 255, 255, 0.7);
        border: 1px solid rgba(99, 102, 241, 0.10);
        border-radius: 16px;
        padding: 14px 20px;
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.03);
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 1.2rem;">📁</span>
            <div>
                <div style="font-size: 0.72rem; color: #64748B; text-transform: uppercase; font-weight: 700;">Storage Artifact Path</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: #6366F1;">{db_path.resolve()}</div>
            </div>
        </div>
        <div style="display: flex; gap: 12px;">
            <span class="badge-pill badge-indigo">Size: {file_size_mb:.2f} MB</span>
            <span class="badge-pill badge-emerald">Engine: DuckDB v1.5</span>
        </div>
    </div>
    """
    st.markdown(info_card, unsafe_allow_html=True)

    if not file_exists:
        st.warning(
            "The database file has not been created yet or has no data. "
            "Process a claim on the 'Process Claim Dossier' view to populate records."
        )
        return

    # ---------------------------------------------------------
    # Sub-tabs for Explorer
    # ---------------------------------------------------------
    tab_browser, tab_360, tab_sql = st.tabs(
        ["📋 Table Browser & Export", "🔍 Claim 360° Dossier Inspector", "⚡ Custom SQL Console"]
    )

    with tab_browser:
        _render_table_browser(counts)
    with tab_360:
        _render_claim_inspector()
    with tab_sql:
        _render_sql_console()


def _render_table_browser(counts: dict[str, int]) -> None:
    st.markdown("### 📋 Browse Tables")

    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([2, 2, 1])
    with ctrl_col1:
        selected_table = st.selectbox(
            "Target Table",
            options=ALL_TABLES,
            format_func=lambda t: f"{t} ({counts.get(t, 0)} records)",
        )
    with ctrl_col2:
        filter_claim = st.text_input("Filter by Claim ID (optional)", placeholder="e.g. CLM-UI-001")
    with ctrl_col3:
        row_limit = st.selectbox("Max Rows", options=[10, 25, 50, 100, 500], index=1)

    try:
        with get_db_connection(read_only=True) as conn:
            query = f"SELECT * FROM {selected_table}"
            params = []
            if filter_claim.strip():
                query += " WHERE claim_id = ?"
                params.append(filter_claim.strip())
            query += f" ORDER BY created_at DESC LIMIT {row_limit}"

            cursor = conn.execute(query, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

            records = [dict(zip(columns, r)) for r in rows]

            if records:
                st.dataframe(records, use_container_width=True)

                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=columns)
                writer.writeheader()
                writer.writerows(records)

                st.download_button(
                    label=f"💾 Download {selected_table}.csv ({len(records)} rows)",
                    data=output.getvalue(),
                    file_name=f"{selected_table}_export.csv",
                    mime="text/csv",
                )
            else:
                st.info(f"No records found in table `{selected_table}`.")
    except Exception as exc:
        st.error(f"Error fetching table data: {exc}")


def _render_claim_inspector() -> None:
    st.markdown("### 🔍 360° Comprehensive Claim Dossier")

    claim_ids = []
    try:
        with get_db_connection(read_only=True) as conn:
            res = conn.execute("SELECT DISTINCT claim_id FROM claims ORDER BY claim_id DESC").fetchall()
            claim_ids = [r[0] for r in res]
    except Exception:
        pass

    if not claim_ids:
        st.info("No claims found in the database yet. Process a claim first!")
        return

    selected_claim_id = st.selectbox("Select Claim ID to Inspect:", options=claim_ids)

    if not selected_claim_id:
        return

    with get_db_connection(read_only=True) as conn:
        # 1. Claim info
        claim_row = conn.execute(
            "SELECT * FROM claims WHERE claim_id = ?", [selected_claim_id]
        ).fetchone()
        if claim_row:
            cols = [c[0] for c in conn.description]
            claim_dict = dict(zip(cols, claim_row))

            st.markdown(
                f"""
                <div class="glass-card" style="margin-top: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h4 style="margin: 0; color: #1E293B; font-weight: 700;">Claim Metadata: {claim_dict.get('claim_id')}</h4>
                        <span class="badge-pill badge-cyan">Status: {claim_dict.get('status')}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; font-size: 0.9rem;">
                        <div><span style="color: #64748B;">Policy Number:</span> <strong style="color: #1E293B;">{claim_dict.get('policy_number') or '—'}</strong></div>
                        <div><span style="color: #64748B;">Claimant:</span> <strong style="color: #1E293B;">{claim_dict.get('claimant_name') or '—'}</strong></div>
                        <div><span style="color: #64748B;">Vehicle Reg:</span> <strong style="color: #1E293B;">{claim_dict.get('vehicle_registration') or '—'}</strong></div>
                        <div><span style="color: #64748B;">Incident Date:</span> <strong style="color: #1E293B;">{claim_dict.get('incident_date') or '—'}</strong></div>
                        <div><span style="color: #64748B;">Reported Date:</span> <strong style="color: #1E293B;">{claim_dict.get('reported_date') or '—'}</strong></div>
                        <div><span style="color: #64748B;">Created At:</span> <strong style="color: #1E293B;">{claim_dict.get('created_at') or '—'}</strong></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # 2. Documents
        doc_rows = conn.execute(
            "SELECT document_id, document_type, file_name, created_at FROM documents WHERE claim_id = ?",
            [selected_claim_id],
        ).fetchall()
        if doc_rows:
            st.markdown("#### 📂 Attached Documents Catalog")
            st.dataframe(
                [dict(zip(["Document ID", "Type", "File Name", "Created At"], r)) for r in doc_rows],
                use_container_width=True,
            )

        # 3. Extracted Evidence
        ev_rows = conn.execute(
            """
            SELECT field_name, field_value, confidence, page_number, evidence_text
            FROM extracted_evidence
            WHERE claim_id = ?
            ORDER BY field_name ASC
            """,
            [selected_claim_id],
        ).fetchall()
        if ev_rows:
            st.markdown("#### 🔎 Extracted Evidence & OCR Text Anchors")
            st.dataframe(
                [dict(zip(["Field Name", "Value", "Confidence", "Page", "Text Snippet"], r)) for r in ev_rows],
                use_container_width=True,
            )

        # 4. Invariant Results
        inv_rows = conn.execute(
            """
            SELECT invariant_id, result, severity, explanation
            FROM invariant_results
            WHERE claim_id = ?
            ORDER BY invariant_id ASC
            """,
            [selected_claim_id],
        ).fetchall()
        if inv_rows:
            st.markdown("#### ⚖️ Consistency & Fraud Invariant Checks")
            st.dataframe(
                [dict(zip(["Invariant Rule", "Result", "Severity", "Explanation"], r)) for r in inv_rows],
                use_container_width=True,
            )

        # 5. Policy Results
        pol_rows = conn.execute(
            """
            SELECT rule_id, result, explanation, repair_cost, coverage_limit, deductible, estimated_payable
            FROM policy_evaluations
            WHERE claim_id = ?
            ORDER BY rule_id ASC
            """,
            [selected_claim_id],
        ).fetchall()
        if pol_rows:
            st.markdown("#### 📜 Policy Compliance Evaluations")
            formatted_pol = []
            for r in pol_rows:
                rule, res, exp, cost, limit, ded, payable = r
                formatted_pol.append({
                    "Rule": rule,
                    "Result": res,
                    "Explanation": exp or "—",
                    "Cost": f"₹{cost:,.2f}" if cost is not None else "—",
                    "Limit": f"₹{limit:,.2f}" if limit is not None else "—",
                    "Deductible": f"₹{ded:,.2f}" if ded is not None else "—",
                    "Payable": f"₹{payable:,.2f}" if payable is not None else "—",
                })
            st.dataframe(formatted_pol, use_container_width=True)


def _render_sql_console() -> None:
    st.markdown("### ⚡ Live SQL Console")
    st.caption("Execute read-only SQL queries directly against the DuckDB audit lake.")

    sample_sql = "SELECT claim_id, claimant_name, vehicle_registration, status, created_at FROM claims ORDER BY created_at DESC LIMIT 10;"
    user_query = st.text_area("SQL Statement", value=sample_sql, height=110)

    if st.button("▶️ Execute Query", type="primary"):
        if not user_query.strip():
            st.warning("Please enter a SQL query.")
            return

        try:
            with get_db_connection(read_only=True) as conn:
                cursor = conn.execute(user_query)
                if cursor.description:
                    columns = [col[0] for col in cursor.description]
                    rows = cursor.fetchall()
                    records = [dict(zip(columns, r)) for r in rows]
                    st.success(f"Returned {len(records)} row(s).")
                    if records:
                        st.dataframe(records, use_container_width=True)
                    else:
                        st.info("Query executed successfully. 0 rows returned.")
                else:
                    st.success("Query executed successfully.")
        except Exception as exc:
            st.error(f"SQL Execution Error: {exc}")
