from pathlib import Path

from src.models.schemas import ClaimAssessment


class ReportService:
    """Generate a human-readable claim assessment report."""

    def generate_text_report(
        self,
        assessment: ClaimAssessment,
        output_path: str | None = None,
    ) -> str:

        lines = []

        lines.append("=" * 70)
        lines.append("CLAIMGUARD-MCP CLAIM ASSESSMENT REPORT")
        lines.append("=" * 70)

        lines.append("")
        lines.append(f"Claim ID: {assessment.claim_id}")
        lines.append(f"Overall Result: {assessment.overall_result}")
        lines.append(f"Evidence Count: {assessment.evidence_count}")

        # ---------------------------------------------------------
        # Policy Evaluation
        # ---------------------------------------------------------
        lines.append("")
        lines.append("POLICY EVALUATION")
        lines.append("-" * 70)

        for result in assessment.policy_results:
            lines.append(
                f"[{result.result}] "
                f"{result.rule_id}: "
                f"{result.explanation or ''}"
            )

        # ---------------------------------------------------------
        # Cross-Document Consistency
        # ---------------------------------------------------------
        lines.append("")
        lines.append("CROSS-DOCUMENT CONSISTENCY")
        lines.append("-" * 70)

        for result in assessment.invariant_results:
            lines.append(
                f"[{result.result}] "
                f"{result.invariant_id}: "
                f"{result.explanation or ''}"
            )

        # ---------------------------------------------------------
        # Expense Evaluation
        # ---------------------------------------------------------
        lines.append("")
        lines.append("EXPENSE EVALUATION")
        lines.append("-" * 70)

        for result in assessment.expense_results:
            lines.append(
                f"[{result.result}] "
                f"{result.rule_id}: "
                f"{result.explanation or ''}"
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
            lines.append("")
            lines.append("FINANCIAL SUMMARY")
            lines.append("-" * 70)

            if financial_result.repair_cost is not None:
                lines.append(
                    f"Repair Cost: "
                    f"₹{financial_result.repair_cost:,.2f}"
                )

            if financial_result.coverage_limit is not None:
                lines.append(
                    f"Coverage Limit: "
                    f"₹{financial_result.coverage_limit:,.2f}"
                )

            if financial_result.deductible is not None:
                lines.append(
                    f"Deductible: "
                    f"₹{financial_result.deductible:,.2f}"
                )

            if financial_result.estimated_payable is not None:
                lines.append(
                    f"Estimated Payable: "
                    f"₹{financial_result.estimated_payable:,.2f}"
                )

        # ---------------------------------------------------------
        # Damage Evaluation
        # ---------------------------------------------------------
        lines.append("")
        lines.append("DAMAGE CONSISTENCY")
        lines.append("-" * 70)

        for result in assessment.damage_results:
            lines.append(
                f"[{result.result}] "
                f"{result.invariant_id}: "
                f"{result.explanation or ''}"
            )

        # ---------------------------------------------------------
        # Document Completeness
        # ---------------------------------------------------------
        lines.append("")
        lines.append("DOCUMENT COMPLETENESS")
        lines.append("-" * 70)

        if assessment.missing_documents:
            for document in assessment.missing_documents:
                lines.append(f"[MISSING] {document}")
        else:
            lines.append("[OK] All required documents are present.")

        # ---------------------------------------------------------
        # Reasons
        # ---------------------------------------------------------
        lines.append("")
        lines.append("ASSESSMENT REASONS")
        lines.append("-" * 70)

        if assessment.reasons:
            for reason in assessment.reasons:
                lines.append(f"- {reason}")
        else:
            lines.append("No additional review reasons.")

        lines.append("")
        lines.append("=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)

        report = "\n".join(lines)

        if output_path is not None:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(
                report,
                encoding="utf-8",
            )

        return report