"""
Generate ClaimGuard-MCP Review II PowerPoint Presentation
Matches the LTIMindtree / L&T EduTech Review II template specification:
- Calibri font throughout
- Title: 36pt
- Subtitles / Headers: 28pt
- Body points: 20-24pt
- Top Right: Project Title - Calibri 18pt
"""

import sys
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    print("python-pptx is not installed. Run: pip install python-pptx")
    sys.exit(0)


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 widescreen
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]

    # Colors
    NAVY_DARK = RGBColor(10, 54, 99)
    TEAL_ACCENT = RGBColor(27, 122, 158)
    GREEN_LINE = RGBColor(56, 176, 0)
    DARK_TEXT = RGBColor(33, 37, 41)
    MUTED_TEXT = RGBColor(108, 117, 125)
    WHITE = RGBColor(255, 255, 255)
    BOX_BG = RGBColor(241, 245, 249)
    BOX_BORDER = RGBColor(203, 213, 225)

    def add_header(slide, title_text):
        # Top-right project title
        tr_box = slide.shapes.add_textbox(Inches(7.5), Inches(0.2), Inches(5.3), Inches(0.5))
        tf_tr = tr_box.text_frame
        tf_tr.word_wrap = True
        p_tr = tf_tr.paragraphs[0]
        p_tr.text = "ClaimGuard-MCP - Calibri body 18"
        p_tr.font.name = "Calibri"
        p_tr.font.size = Pt(18)
        p_tr.font.color.rgb = TEAL_ACCENT
        p_tr.alignment = PP_ALIGN.RIGHT

        # Slide Main Title
        title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(11.5), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.name = "Calibri"
        p_title.font.size = Pt(36)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY_DARK

        # Accent Line
        line = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.3), Inches(8.5), Inches(0.04)
        )
        line.fill.solid()
        line.fill.fore_color.rgb = GREEN_LINE
        line.line.color.rgb = GREEN_LINE

        # Footer Left (L&T EduTech)
        lt_box = slide.shapes.add_textbox(Inches(0.6), Inches(6.8), Inches(3.0), Inches(0.4))
        p_lt = lt_box.text_frame.paragraphs[0]
        p_lt.text = "L&T EduTech"
        p_lt.font.name = "Calibri"
        p_lt.font.size = Pt(14)
        p_lt.font.bold = True
        p_lt.font.color.rgb = NAVY_DARK

        # Footer Right (LTIMindtree)
        lti_box = slide.shapes.add_textbox(Inches(9.5), Inches(6.8), Inches(3.2), Inches(0.4))
        p_lti = lti_box.text_frame.paragraphs[0]
        p_lti.text = "LTIMindtree"
        p_lti.font.name = "Calibri"
        p_lti.font.size = Pt(14)
        p_lti.font.bold = True
        p_lti.font.color.rgb = TEAL_ACCENT
        p_lti.alignment = PP_ALIGN.RIGHT

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = NAVY_DARK
    bg1.line.color.rgb = NAVY_DARK

    tbox1 = slide1.shapes.add_textbox(Inches(1.0), Inches(0.5), Inches(11.3), Inches(6.5))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "M.Tech/MCA Program"
    p.font.name = "Calibri"
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    p = tf1.add_paragraph()
    p.text = "Advanced Industry Integrated Programs"
    p.font.name = "Calibri"
    p.font.size = Pt(20)
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    p = tf1.add_paragraph()
    p.text = "Jointly offered by University and LTIMindTree\n"
    p.font.name = "Calibri"
    p.font.size = Pt(14)
    p.font.color.rgb = RGBColor(220, 230, 242)
    p.alignment = PP_ALIGN.CENTER

    p = tf1.add_paragraph()
    p.text = "Review II"
    p.font.name = "Calibri"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = RGBColor(144, 224, 239)
    p.alignment = PP_ALIGN.CENTER

    p = tf1.add_paragraph()
    p.text = "ClaimGuard-MCP: Multimodal Insurance Claim Consistency & Fraud Arbiter"
    p.font.name = "Calibri"
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    p = tf1.add_paragraph()
    p.text = "\nTeam Member: Project Candidate\nCalibri body -24"
    p.font.name = "Calibri"
    p.font.size = Pt(22)
    p.font.color.rgb = WHITE
    p.alignment = PP_ALIGN.CENTER

    # -------------------------------------------------------------
    # SLIDE 2: Introduction
    # -------------------------------------------------------------
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Introduction....")

    box2 = slide2.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    tf2 = box2.text_frame
    tf2.word_wrap = True

    points2 = [
        (
            "Insurance Fraud & Manual Bottlenecks:",
            "Modern motor insurance claims suffer from rampant leakage exceeding $30 billion annually due to fabricated repair estimates and mismatched incident data. Manual cross-verification across police reports, repair bills, and policy schedules is exceedingly slow, error-prone, and labor-intensive."
        ),
        (
            "The Multimodal Arbitration Solution:",
            "ClaimGuard-MCP introduces an automated, end-to-end multimodal validation pipeline that reconciles textual declarations with visual photographic damage evidence. By pairing PyMuPDF and Tesseract OCR with Qwen2-VL vision intelligence, the platform guarantees cross-document consistency."
        ),
        (
            "Agentic Architecture via MCP:",
            "Built upon the Model Context Protocol (MCP), ClaimGuard seamlessly exposes specialized forensic arbitration tools directly to enterprise AI agents. This eliminates operational silos and reduces claim assessment turnarounds from several business days down to seconds."
        ),
    ]
    for i, (head, body) in enumerate(points2):
        p = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(20)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(20)

    # -------------------------------------------------------------
    # SLIDE 3: Objective
    # -------------------------------------------------------------
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "Objective....")

    box3 = slide3.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    tf3 = box3.text_frame
    tf3.word_wrap = True

    points3 = [
        (
            "Automate Heterogeneous Claim Package Ingestion:",
            "Develop an ingestion engine capable of automatically extracting, classifying, and structuring data from diverse formats including claim forms, police FIRs, workshop estimates, and damage photos into validated schemas."
        ),
        (
            "Enforce Zero-Tolerance Invariant & Policy Boundaries:",
            "Implement deterministic rule-based verification to enforce non-negotiable invariants: policy active dates, identity matching, vehicle registration parity, and expense reconciliation (Parts + Labor == Total Claimed)."
        ),
        (
            "Multimodal Damage Arbitration & Explainability:",
            "Corroborate visual damage photographs against written line items using vision-language intelligence, producing an auditable decision (PASS / REVIEW) with transparent, human-readable forensic explanations."
        ),
    ]
    for i, (head, body) in enumerate(points3):
        p = tf3.paragraphs[0] if i == 0 else tf3.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(20)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(22)

    # -------------------------------------------------------------
    # SLIDE 4: System Architecture / Module Breakdown
    # -------------------------------------------------------------
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Module name - System Architecture")

    box4 = slide4.shapes.add_textbox(Inches(0.8), Inches(1.5), Inches(11.7), Inches(5.0))
    tf4 = box4.text_frame
    tf4.word_wrap = True

    points4 = [
        (
            "Ingestion & Optical Character Recognition Module:",
            "Extracts raw text and metadata from structured PDFs using PyMuPDF and utilizes Tesseract OCR for scanned physical documents. Applies keyword classification to map files into typed entities."
        ),
        (
            "Vision Perception & Feature Extraction Module:",
            "Connects to remote Qwen2-VL vision models to analyze exterior vehicle damage photos. Identifies impacted zones, severity level, and checks for contradictions against customer declarations."
        ),
        (
            "Arbitration Engine & Dual Reporting Module:",
            "Executes multi-rule invariant checks, deductible deductions, and coverage limit constraints. Generates comprehensive audit trails exported to DuckDB, Streamlit UI, and PDF reports."
        ),
    ]
    for i, (head, body) in enumerate(points4):
        p = tf4.paragraphs[0] if i == 0 else tf4.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(19)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(16)

    # -------------------------------------------------------------
    # SLIDE 5: Methodology / Modeling Plan
    # -------------------------------------------------------------
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Methodology/Modeling Plan....")

    box5 = slide5.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    tf5 = box5.text_frame
    tf5.word_wrap = True

    points5 = [
        (
            "Neuro-Symbolic Hybrid Architecture:",
            "Combines neural perception (Qwen2-VL vision intelligence) with symbolic deterministic logic (invariant rules). Neural models interpret ambiguous visual damage, while deterministic code verifies policy math."
        ),
        (
            "Invariant Consistency & Reconciliation Rules:",
            "Establishes a zero-trust verification model across 5 distinct dimensions: temporal validity (incident within policy tenure), identity alignment, vehicle registration matching, and financial arithmetic integrity."
        ),
        (
            "Two-Stage Triaging & Decision Matrix:",
            "Claims are evaluated into binary states: PASS (all invariants hold and damage corroborates) or REVIEW. Any discrepancy automatically attaches forensic flags detailing exact inconsistencies for adjuster review."
        ),
    ]
    for i, (head, body) in enumerate(points5):
        p = tf5.paragraphs[0] if i == 0 else tf5.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(20)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(22)

    # -------------------------------------------------------------
    # SLIDE 6: Data Preprocessing & EDA
    # -------------------------------------------------------------
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Data preprocessing & EDA....")

    box6 = slide6.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    tf6 = box6.text_frame
    tf6.word_wrap = True

    points6 = [
        (
            "Text Normalization & Entity Canonicalization:",
            "Preprocesses noisy OCR extracts by removing whitespace artifacts, standardizing vehicle plate formats, and uppercase-normalizing identities and policy keys to prevent false mismatch triggers."
        ),
        (
            "Numerical & Currency Sanitization:",
            "Parses monetary values across different regional conventions (e.g., INR formatting), converting them into standardized floats. Implements epsilon tolerance (abs(diff) < 0.01) to eliminate rounding anomalies."
        ),
        (
            "Image Encoding & Quality Validation:",
            "Inspects submitted image resolutions, verifies valid MIME encodings (PNG/JPEG), and formats base64 payloads with connection retry policies to ensure resilient transmission to the vision inference API."
        ),
    ]
    for i, (head, body) in enumerate(points6):
        p = tf6.paragraphs[0] if i == 0 else tf6.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(20)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(22)

    # -------------------------------------------------------------
    # SLIDE 7: Approach / Algorithms / Tools
    # -------------------------------------------------------------
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Approach/Algorithms/Tools....")

    box7 = slide7.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    tf7 = box7.text_frame
    tf7.word_wrap = True

    points7 = [
        (
            "Core Technologies & Persistence:",
            "Developed using Python 3.11 with Pydantic v2 schemas for strict runtime type safety. Embeds DuckDB using safe context managers for high-performance analytical storage without database server overhead."
        ),
        (
            "Perception & Extraction Libraries:",
            "Leverages PyMuPDF for fast digital PDF document parsing and Tesseract OCR for physical document digitization. Qwen2-VL vision model performs zero-shot vehicular damage inspection."
        ),
        (
            "Agent Integration & User Interface:",
            "Exposes assessment endpoints as MCP tools via FastMCP for agentic orchestration. Delivers an interactive Streamlit UI with live status metrics and automated ReportLab PDF report generation."
        ),
    ]
    for i, (head, body) in enumerate(points7):
        p = tf7.paragraphs[0] if i == 0 else tf7.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(20)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(22)

    # -------------------------------------------------------------
    # SLIDE 8: Project Plan / Milestones Progress
    # -------------------------------------------------------------
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "Project plan/milestones progress")

    box8 = slide8.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    tf8 = box8.text_frame
    tf8.word_wrap = True

    points8 = [
        (
            "Phase 1 & 2 Completed (Data Ingestion & Extraction Engine):",
            "Delivered comprehensive document ingestion for 4 PDF types and damage photos. Implemented rule-based classification and structured extraction mapped to typed Pydantic models."
        ),
        (
            "Phase 3 Completed (Evaluation & Invariant Pipeline):",
            "Engineered policy evaluation, cross-document invariant checks, repair cost consistency calculations, and remote Qwen2-VL vision API integration with complete unit and integration test coverage."
        ),
        (
            "Phase 4 & Review II Status (User Interfaces & Agent Delivery):",
            "Deployed Streamlit interactive dashboard, ReportLab PDF report export, DuckDB session management, and Model Context Protocol (MCP) server endpoints ready for enterprise deployment."
        ),
    ]
    for i, (head, body) in enumerate(points8):
        p = tf8.paragraphs[0] if i == 0 else tf8.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(20)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(22)

    # -------------------------------------------------------------
    # SLIDE 9: Pipeline Structure
    # -------------------------------------------------------------
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Pipeline structure")

    box9 = slide9.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.7), Inches(5.0))
    tf9 = box9.text_frame
    tf9.word_wrap = True

    points9 = [
        (
            "End-to-End Orchestrated Pipeline Flow:",
            "Claim packages enter via CLI, Streamlit, or MCP server. The ClaimPackageService orchestrates parallel extraction, passing text to Ingestion and photos to Vision services before invoking evaluation."
        ),
        (
            "Multi-Stage Arbitration & Synthesis:",
            "The ClaimEvaluationPipeline runs policy validation, invariant checking, expense math, and visual damage comparisons. Results are synthesized into a consolidated ClaimAssessment model."
        ),
        (
            "Artifact Generation & Persistence:",
            "Persists assessment records to DuckDB, displays live metrics on Streamlit, and generates downloadable ASCII text and styled PDF reports containing clear explanations and evidence counts."
        ),
    ]
    for i, (head, body) in enumerate(points9):
        p = tf9.paragraphs[0] if i == 0 else tf9.add_paragraph()
        p.text = f"•  {head} {body}"
        p.font.name = "Calibri"
        p.font.size = Pt(20)
        p.font.color.rgb = DARK_TEXT
        p.space_after = Pt(22)

    output_path = Path("ClaimGuard_MCP_Review_II_Presentation.pptx")
    prs.save(str(output_path))
    print(f"Presentation saved successfully to: {output_path.resolve()}")


if __name__ == "__main__":
    create_deck()
