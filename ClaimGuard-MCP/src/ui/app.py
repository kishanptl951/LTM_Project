import sys
import tempfile
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------
# Project root
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.config import settings
from src.models.schemas import DamagePhotoDocument
from src.orchestration.claim_package_service import ClaimPackageService
from src.reporting import PDFReportService, ReportService
from src.ui.db_viewer import render_db_explorer
from src.ui.theme import (
    inject_custom_css,
    render_brand_header,
    render_check_item,
    render_financial_dossier,
    render_sidebar_status,
    render_verdict_card,
)
from src.vision.vision_extraction_service import VisionExtractionService

# ---------------------------------------------------------
# Page configuration & Styling
# ---------------------------------------------------------

st.set_page_config(
    page_title="ClaimGuard-MCP • Insurance Fraud Arbiter",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()

# ---------------------------------------------------------
# Sidebar Configuration
# ---------------------------------------------------------

st.sidebar.markdown(
    """
    <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
        <span style="font-size: 1.5rem;">🛡️</span>
        <span style="font-weight: 800; font-size: 1.15rem; background: linear-gradient(135deg, #4F46E5, #7C3AED); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">ClaimGuard</span>
        <span class="badge-pill badge-indigo" style="font-size: 0.65rem;">MCP</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Navigation")
app_mode = st.sidebar.radio(
    "Select Console View:",
    ["📋 Process Claim Dossier", "🗄️ Backend Database Explorer"],
    index=0,
)

st.sidebar.divider()

if app_mode == "🗄️ Backend Database Explorer":
    render_db_explorer()
    st.stop()

st.sidebar.header("Vision AI Engine")
vision_mode = st.sidebar.radio(
    "Damage Photo Model:",
    options=[
        "Demo / Simulation Mode",
        "Remote Qwen2-VL Server",
        "Manual Review / Skip Vision",
    ],
    index=0,
    help="Select how vehicle damage images are processed by the multimodal neural net.",
)

custom_vision_url = ""
if vision_mode == "Remote Qwen2-VL Server":
    custom_vision_url = st.sidebar.text_input(
        "Vision API Endpoint URL",
        value=settings.vision_api_url or "",
        placeholder="http://localhost:8000",
        help="Base URL of your deployed Qwen2-VL inference server.",
    )
    if not custom_vision_url.strip():
        st.sidebar.warning("No Vision API URL entered. Damage photo check will default to manual review.")

st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="font-size: 0.8rem; color: #64748B; background: rgba(238, 242, 255, 0.5); border: 1px solid rgba(99, 102, 241, 0.08); border-radius: 12px; padding: 12px;">
        <strong style="color: #334155;">📁 Sample Dossier Pack:</strong><br>
        <code style="color: #6366F1; font-size: 0.75rem;">data/sample_claims/realistic_package/</code><br>
        <span style="color: #475569;">• claim_form.pdf<br>
        • policy.pdf<br>
        • police_report.pdf<br>
        • repair_estimate.pdf<br>
        • damage_photo.jpg</span>
    </div>
    """,
    unsafe_allow_html=True,
)

render_sidebar_status()


# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------


def get_vision_service() -> VisionExtractionService:
    if vision_mode == "Demo / Simulation Mode":

        class DemoVisionExtractionService(VisionExtractionService):

            def extract_damage(
                self,
                file_path: str,
                claim_id: str | None = None,
            ) -> DamagePhotoDocument:
                self.validate_image(file_path)
                return self.create_damage_document(
                    claim_id=claim_id,
                    vehicle_registration="TS09AB1234",
                    photo_description=(
                        "A vehicle with front-end damage to the bumper and headlights."
                    ),
                    damage_area="front end",
                    visible_damage="damaged front bumper and headlights",
                    estimated_severity="severe",
                )

        return DemoVisionExtractionService()
    elif vision_mode == "Remote Qwen2-VL Server":
        return VisionExtractionService(
            vision_api_url=custom_vision_url.strip()
        )
    else:
        return VisionExtractionService(vision_api_url="")


def render_assessment_dossier(assessment) -> None:
    render_verdict_card(assessment)

    # Top KPI Metrics
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Policy Tests", len(assessment.policy_results))
    with kpi2:
        st.metric("Invariants Checked", len(assessment.invariant_results))
    with kpi3:
        st.metric("Expense Rules", len(assessment.expense_results))
    with kpi4:
        st.metric("Evidence Snippets", assessment.evidence_count or 0)

    # Financial settlement dossier
    financial_result = next(
        (
            res
            for res in assessment.expense_results
            if res.rule_id == "REPAIR_COST_WITHIN_COVERAGE"
        ),
        None,
    )
    if financial_result:
        render_financial_dossier(financial_result)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # Detailed Audit Breakdown in Glass Tabs
    tab_pol, tab_inv, tab_exp, tab_dam, tab_doc, tab_reasons = st.tabs(
        [
            f"📜 Policy Rules ({len(assessment.policy_results)})",
            f"⚖️ Invariants ({len(assessment.invariant_results)})",
            f"🛠️ Expenses ({len(assessment.expense_results)})",
            f"📸 Vision & Damage ({len(assessment.damage_results)})",
            "📁 Required Docs",
            f"🚨 Flags & Notes ({len(assessment.reasons)})",
        ]
    )

    with tab_pol:
        st.markdown(
            "#### Policy Period, Registration & Coverage Rules"
        )
        for res in assessment.policy_results:
            render_check_item(
                res.rule_id,
                res.explanation or "No explanation provided.",
                res.result,
            )

    with tab_inv:
        st.markdown("#### Cross-Document Consistency & Registration Invariants")
        for res in assessment.invariant_results:
            render_check_item(
                res.invariant_id,
                res.explanation or "No explanation provided.",
                res.result,
            )

    with tab_exp:
        st.markdown("#### Expense & Parts/Labor Arithmetic Consistency")
        for res in assessment.expense_results:
            render_check_item(
                res.rule_id,
                res.explanation or "No explanation provided.",
                res.result,
            )

    with tab_dam:
        st.markdown("#### Damage Area Correlation vs Incident Description")
        for res in assessment.damage_results:
            render_check_item(
                res.invariant_id,
                res.explanation or "No explanation provided.",
                res.result,
            )

    with tab_doc:
        st.markdown("#### Document Package Completeness Verification")
        if assessment.missing_documents:
            for doc in assessment.missing_documents:
                render_check_item(
                    f"MISSING: {doc}",
                    f"Required document '{doc}' is absent from the claim package.",
                    "REVIEW",
                )
        else:
            render_check_item(
                "DOCUMENT_PACKAGE_COMPLETE",
                "All mandatory insurance claim documents are present and catalogued.",
                "PASS",
            )

    with tab_reasons:
        st.markdown("#### Adjuster Action Items & Attention Flags")
        if assessment.reasons:
            for reason in assessment.reasons:
                st.markdown(
                    f"""
                    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(251, 191, 36, 0.04)); border-left: 4px solid #F59E0B; padding: 12px 16px; border-radius: 12px; margin-bottom: 10px; color: #92400E; font-size: 0.9rem; font-weight: 500;">
                        ⚠️ {reason}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.success("Zero review flags. Clean claim suitable for Straight-Through Processing (STP).")

    # Export Section
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📑 Export Audit Dossier", help="Download your assessment in text or formal PDF format.")

    report_service = ReportService()
    text_report = report_service.generate_text_report(assessment)

    pdf_service = PDFReportService()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_path = tmp_pdf.name
    try:
        pdf_service.generate_pdf_report(assessment, pdf_path)
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
    finally:
        Path(pdf_path).unlink(missing_ok=True)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            label="📄 Download Text Dossier (.txt)",
            data=text_report,
            file_name=f"{assessment.claim_id}_audit_report.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            label="📑 Download Formal PDF Report (.pdf)",
            data=pdf_bytes,
            file_name=f"{assessment.claim_id}_audit_report.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# ---------------------------------------------------------
# Main Page Header
# ---------------------------------------------------------

render_brand_header()

# ---------------------------------------------------------
# Claim Ingestion Box
# ---------------------------------------------------------

st.markdown('<div class="glass-card">', unsafe_allow_html=True)
st.markdown(
    """
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.3rem;">📋</span>
            <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700; color: #1E293B;">Claim Dossier Ingestion</h3>
        </div>
        <span class="badge-pill badge-cyan">Automated Triage</span>
    </div>
    """,
    unsafe_allow_html=True,
)

col_in1, col_in2 = st.columns([2, 1])

with col_in1:
    claim_id_input = st.text_input(
        "Claim Reference ID",
        value="CLM-UI-001",
        placeholder="e.g. CLM-2026-001",
        help="Unique insurance claim reference number to catalogue in DuckDB.",
    )

with col_in2:
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    quick_sample_clicked = st.button(
        "⚡ 1-Click Load Realistic Package",
        use_container_width=True,
        help="Instantly evaluate the bundled realistic claim package (Claim Form, Policy, Police FIR, Repair Estimate, Damage Photo).",
    )

uploaded_files = st.file_uploader(
    "Upload Claim Package Files (PDFs, Images, Estimates, Police FIR)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="Upload claim form, policy contract, police report, repair estimate, and damage photographs.",
)

if uploaded_files:
    st.markdown(
        "<div style='margin-top: 10px; margin-bottom: 15px; display: flex; gap: 8px; flex-wrap: wrap;'>",
        unsafe_allow_html=True,
    )
    for file in uploaded_files:
        st.markdown(
            f"<span class='badge-pill badge-indigo'>📄 {file.name}</span>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

analyze_clicked = st.button(
    "🚀 Analyze & Arbitrate Claim Dossier",
    type="primary",
    use_container_width=True,
)

st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# Execution Handlers
# ---------------------------------------------------------

if quick_sample_clicked:
    sample_dir = PROJECT_ROOT / "data" / "sample_claims" / "realistic_package"
    if not sample_dir.exists():
        st.error(f"Sample directory not found: {sample_dir}")
    else:
        with st.spinner("🤖 Running Multimodal Neural Extraction & Invariant Arbitration..."):
            try:
                vision_service = get_vision_service()
                service = ClaimPackageService(
                    vision_extraction_service=vision_service
                )
                assessment = service.process_package(
                    package_path=str(sample_dir),
                    claim_id="CLM-REALISTIC-001",
                )
                st.session_state["latest_assessment"] = assessment
                st.success("✅ Sample Claim Package Analyzed & Stored in DuckDB!")
            except Exception as exc:
                st.error("Analysis failed.")
                st.exception(exc)

elif analyze_clicked:
    if not claim_id_input.strip():
        st.error("Please enter a valid Claim ID.")
        st.stop()

    if not uploaded_files:
        st.error("Please upload at least one claim document or click '⚡ 1-Click Load Realistic Package'.")
        st.stop()

    with tempfile.TemporaryDirectory() as temp_dir:
        package_path = Path(temp_dir)

        for uploaded_file in uploaded_files:
            file_path = package_path / uploaded_file.name
            with open(file_path, "wb") as output_file:
                output_file.write(uploaded_file.getbuffer())

        with st.spinner("🤖 Processing Claim Package & Checking Cross-Document Invariants..."):
            try:
                vision_service = get_vision_service()
                service = ClaimPackageService(
                    vision_extraction_service=vision_service
                )
                assessment = service.process_package(
                    package_path=str(package_path),
                    claim_id=claim_id_input.strip(),
                )
                st.session_state["latest_assessment"] = assessment
                st.success("✅ Claim Evaluation Complete & Logged in DuckDB!")
            except Exception as exc:
                st.error("Claim analysis failed.")
                st.exception(exc)
                st.stop()


# ---------------------------------------------------------
# Render Assessment Output
# ---------------------------------------------------------

if "latest_assessment" in st.session_state:
    render_assessment_dossier(st.session_state["latest_assessment"])


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.divider()
st.markdown(
    """
    <div style="
        display: flex; justify-content: space-between; align-items: center;
        color: #94A3B8; font-size: 0.78rem; padding: 14px 20px;
        background: rgba(255, 255, 255, 0.5);
        border: 1px solid rgba(99, 102, 241, 0.06);
        border-radius: 14px;
        backdrop-filter: blur(8px);
    ">
        <div>🛡️ ClaimGuard-MCP • Enterprise Multimodal Fraud Arbitration Terminal</div>
        <div>DuckDB Embedded Lake • FastMCP Agent Layer</div>
    </div>
    """,
    unsafe_allow_html=True,
)