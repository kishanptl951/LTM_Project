from src.models.schemas import (
    Claim,
    ClaimAssessment,
    InvariantResult,
    PolicyEvaluation,
)


class ClaimAssessmentService:

    def assess_claim(
        self,
        claim: Claim,
        policy_results: list[PolicyEvaluation],
        invariant_results: list[InvariantResult],
        expense_results: list[PolicyEvaluation] | None = None,
        damage_results: list[InvariantResult] | None = None,
        evidence_count: int = 0,
        required_documents: list[str] | None = None,
        available_documents: list[str] | None = None,
        missing_documents: list[str] | None = None,
    ) -> ClaimAssessment:

        reasons = []

        required_documents = required_documents or []
        available_documents = available_documents or []
        missing_documents = missing_documents or []
        expense_results = expense_results or []
        damage_results = damage_results or []

        # ---------------------------------------------------------
        # Policy evaluation results
        # ---------------------------------------------------------
        for result in policy_results:
            if result.result in {"FAIL", "REVIEW"}:
                reasons.append(
                    result.explanation
                    or (
                        "Policy rule requires attention: "
                        f"{result.rule_id}"
                    )
                )

        # ---------------------------------------------------------
        # Cross-document invariant results
        # ---------------------------------------------------------
        for result in invariant_results:
            if result.result in {"FAIL", "REVIEW"}:
                reasons.append(
                    result.explanation
                    or (
                        "Consistency check requires attention: "
                        f"{result.invariant_id}"
                    )
                )

        # ---------------------------------------------------------
        # Expense evaluation results
        # ---------------------------------------------------------
        for result in expense_results:
            if result.result in {"FAIL", "REVIEW"}:
                reasons.append(
                    result.explanation
                    or (
                        "Expense evaluation requires attention: "
                        f"{result.rule_id}"
                    )
                )

        # ---------------------------------------------------------
        # Damage consistency results
        # ---------------------------------------------------------
        for result in damage_results:
            if result.result in {"FAIL", "REVIEW"}:
                reasons.append(
                    result.explanation
                    or (
                        "Damage consistency check requires attention: "
                        f"{result.invariant_id}"
                    )
                )

        # ---------------------------------------------------------
        # Missing required documents
        # ---------------------------------------------------------
        for document in missing_documents:
            reasons.append(
                f"Required document is missing: {document}"
            )

        # ---------------------------------------------------------
        # Determine overall result
        # ---------------------------------------------------------
        has_failures = any(
            result.result == "FAIL"
            for result in (
                policy_results
                + invariant_results
                + expense_results
                + damage_results
            )
        )

        has_review = any(
            result.result == "REVIEW"
            for result in (
                policy_results
                + invariant_results
                + expense_results
                + damage_results
            )
        )

        has_missing_documents = len(missing_documents) > 0

        if has_failures:
            overall_result = "FAIL"
        elif has_review or has_missing_documents:
            overall_result = "REVIEW"
        else:
            overall_result = "PASS"

        # ---------------------------------------------------------
        # Build final assessment
        # ---------------------------------------------------------
        return ClaimAssessment(
            claim_id=claim.claim_id,
            overall_result=overall_result,
            policy_results=policy_results,
            invariant_results=invariant_results,
            expense_results=expense_results,
            damage_results=damage_results,
            reasons=reasons,
            evidence_count=evidence_count,
            required_documents=required_documents,
            available_documents=available_documents,
            missing_documents=missing_documents,
        )