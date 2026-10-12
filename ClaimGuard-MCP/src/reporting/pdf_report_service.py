from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)

from src.models.schemas import ClaimAssessment


class PDFReportService:
    """Generate a professional PDF claim assessment report."""

    def generate_pdf_report(
        self,
        assessment: ClaimAssessment,
        output_path: str,
    ) -> str:

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        document = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
            title="ClaimGuard-MCP Claim Assessment Report",
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            spaceAfter=8,
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            alignment=TA_CENTER,
            fontSize=10,
            spaceAfter=18,
        )

        section_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            spaceBefore=12,
            spaceAfter=8,
        )

        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=13,
            spaceAfter=4,
        )

        story = []

        # ---------------------------------------------------------
        # Header
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "CLAIMGUARD-MCP",
                title_style,
            )
        )

        story.append(
            Paragraph(
                "Insurance Claim Assessment Report",
                subtitle_style,
            )
        )

        # ---------------------------------------------------------
        # Claim Summary
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "Claim Summary",
                section_style,
            )
        )

        summary_data = [
            ["Claim ID", assessment.claim_id],
            ["Overall Result", assessment.overall_result],
            ["Evidence Count", str(assessment.evidence_count)],
        ]

        summary_table = Table(
            summary_data,
            colWidths=[45 * mm, 125 * mm],
        )

        summary_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        story.append(summary_table)

        # ---------------------------------------------------------
        # Policy Evaluation
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "Policy Evaluation",
                section_style,
            )
        )

        for result in assessment.policy_results:
            story.append(
                Paragraph(
                    f"<b>[{result.result}] {result.rule_id}</b><br/>"
                    f"{result.explanation or ''}",
                    body_style,
                )
            )

        # ---------------------------------------------------------
        # Cross-Document Consistency
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "Cross-Document Consistency",
                section_style,
            )
        )

        for result in assessment.invariant_results:
            story.append(
                Paragraph(
                    f"<b>[{result.result}] {result.invariant_id}</b><br/>"
                    f"{result.explanation or ''}",
                    body_style,
                )
            )

        # ---------------------------------------------------------
        # Financial Summary
        # ---------------------------------------------------------

        financial_result = next(
            (
                result
                for result in assessment.expense_results
                if result.rule_id == "REPAIR_COST_WITHIN_COVERAGE"
            ),
            None,
        )

        if financial_result is not None:
            story.append(
                Paragraph(
                    "Financial Summary",
                    section_style,
                )
            )

            financial_data = [
                ["Financial Item", "Amount"],
            ]

            if financial_result.repair_cost is not None:
                financial_data.append(
                    [
                        "Repair Cost",
                        f"₹{financial_result.repair_cost:,.2f}",
                    ]
                )

            if financial_result.coverage_limit is not None:
                financial_data.append(
                    [
                        "Coverage Limit",
                        f"₹{financial_result.coverage_limit:,.2f}",
                    ]
                )

            if financial_result.deductible is not None:
                financial_data.append(
                    [
                        "Deductible",
                        f"₹{financial_result.deductible:,.2f}",
                    ]
                )

            if financial_result.estimated_payable is not None:
                financial_data.append(
                    [
                        "Estimated Payable",
                        f"₹{financial_result.estimated_payable:,.2f}",
                    ]
                )

            financial_table = Table(
                financial_data,
                colWidths=[100 * mm, 70 * mm],
            )

            financial_table.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        (
                            "BACKGROUND",
                            (0, 0),
                            (-1, 0),
                            colors.lightgrey,
                        ),
                        (
                            "FONTNAME",
                            (0, 0),
                            (-1, 0),
                            "Helvetica-Bold",
                        ),
                        (
                            "ALIGN",
                            (1, 1),
                            (1, -1),
                            "RIGHT",
                        ),
                        (
                            "PADDING",
                            (0, 0),
                            (-1, -1),
                            6,
                        ),
                    ]
                )
            )

            story.append(financial_table)

        # ---------------------------------------------------------
        # Expense Evaluation
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "Expense Evaluation",
                section_style,
            )
        )

        for result in assessment.expense_results:
            story.append(
                Paragraph(
                    f"<b>[{result.result}] {result.rule_id}</b><br/>"
                    f"{result.explanation or ''}",
                    body_style,
                )
            )

        # ---------------------------------------------------------
        # Damage Consistency
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "Damage Consistency",
                section_style,
            )
        )

        for result in assessment.damage_results:
            story.append(
                Paragraph(
                    f"<b>[{result.result}] {result.invariant_id}</b><br/>"
                    f"{result.explanation or ''}",
                    body_style,
                )
            )

        # ---------------------------------------------------------
        # Document Completeness
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "Document Completeness",
                section_style,
            )
        )

        if assessment.missing_documents:
            for document_name in assessment.missing_documents:
                story.append(
                    Paragraph(
                        f"<b>[MISSING]</b> {document_name}",
                        body_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    "[OK] All required documents are present.",
                    body_style,
                )
            )

        # ---------------------------------------------------------
        # Assessment Reasons
        # ---------------------------------------------------------

        story.append(
            Paragraph(
                "Assessment Reasons",
                section_style,
            )
        )

        if assessment.reasons:
            for reason in assessment.reasons:
                story.append(
                    Paragraph(
                        f"- {reason}",
                        body_style,
                    )
                )
        else:
            story.append(
                Paragraph(
                    "No additional review reasons.",
                    body_style,
                )
            )

        # ---------------------------------------------------------
        # Footer
        # ---------------------------------------------------------

        story.append(Spacer(1, 12))

        story.append(
            Paragraph(
                "Generated by ClaimGuard-MCP",
                subtitle_style,
            )
        )

        document.build(story)

        return str(output_file)