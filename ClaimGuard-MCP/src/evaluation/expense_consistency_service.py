from uuid import uuid4

from src.models.schemas import (
    PolicyEvaluation,
    RepairEstimateDocument,
)


class ExpenseConsistencyService:

    def validate_repair_estimate(
        self,
        repair_estimate: RepairEstimateDocument,
    ) -> PolicyEvaluation:

        total_cost = repair_estimate.total_estimated_cost
        parts_cost = repair_estimate.parts_cost
        labor_cost = repair_estimate.labor_cost

        if total_cost is None:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=repair_estimate.claim_id or "UNKNOWN",
                rule_id="REPAIR_COST_COMPONENTS_MATCH_TOTAL",
                result="REVIEW",
                explanation=(
                    "Total repair cost is missing."
                ),
            )

        if parts_cost is None:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=repair_estimate.claim_id or "UNKNOWN",
                rule_id="REPAIR_COST_COMPONENTS_MATCH_TOTAL",
                result="REVIEW",
                explanation=(
                    "Parts cost is missing from the repair estimate."
                ),
            )

        if labor_cost is None:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=repair_estimate.claim_id or "UNKNOWN",
                rule_id="REPAIR_COST_COMPONENTS_MATCH_TOTAL",
                result="REVIEW",
                explanation=(
                    "Labor cost is missing from the repair estimate."
                ),
            )

        calculated_total = parts_cost + labor_cost

        if abs(calculated_total - total_cost) > 0.01:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=repair_estimate.claim_id or "UNKNOWN",
                rule_id="REPAIR_COST_COMPONENTS_MATCH_TOTAL",
                result="REVIEW",
                explanation=(
                    f"Parts cost of {parts_cost:.2f} and labor cost "
                    f"of {labor_cost:.2f} do not match the total "
                    f"repair cost of {total_cost:.2f}. "
                    f"Calculated total is {calculated_total:.2f}."
                ),
            )

        return PolicyEvaluation(
            evaluation_id=str(uuid4()),
            claim_id=repair_estimate.claim_id or "UNKNOWN",
            rule_id="REPAIR_COST_COMPONENTS_MATCH_TOTAL",
            result="PASS",
            explanation=(
                f"Parts cost of {parts_cost:.2f} plus labor cost "
                f"of {labor_cost:.2f} matches the total repair "
                f"cost of {total_cost:.2f}."
            ),
        )