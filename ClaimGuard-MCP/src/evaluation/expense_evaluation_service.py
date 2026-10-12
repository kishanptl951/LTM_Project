from uuid import uuid4

from src.models.schemas import (
    Claim,
    PolicyDocument,
    PolicyEvaluation,
    RepairEstimateDocument,
)


class ExpenseEvaluationService:

    def evaluate_repair_cost(
        self,
        claim: Claim,
        policy: PolicyDocument,
        repair_estimate: RepairEstimateDocument,
    ) -> PolicyEvaluation:

        repair_cost = repair_estimate.total_estimated_cost
        coverage_limit = policy.coverage_limit
        deductible = policy.deductible or 0.0

        # Required financial information is missing.
        if repair_cost is None:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=claim.claim_id,
                rule_id="REPAIR_COST_WITHIN_COVERAGE",
                result="REVIEW",
                explanation=(
                    "Repair cost is missing from the repair estimate."
                ),
            )

        if coverage_limit is None:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=claim.claim_id,
                rule_id="REPAIR_COST_WITHIN_COVERAGE",
                result="REVIEW",
                explanation=(
                    "Policy coverage limit is missing."
                ),
            )

        # Invalid negative values should never be treated as valid costs.
        if repair_cost < 0:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=claim.claim_id,
                rule_id="REPAIR_COST_WITHIN_COVERAGE",
                result="REVIEW",
                explanation=(
                    "Repair cost cannot be negative."
                ),
            )

        if coverage_limit < 0:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=claim.claim_id,
                rule_id="REPAIR_COST_WITHIN_COVERAGE",
                result="REVIEW",
                explanation=(
                    "Policy coverage limit cannot be negative."
                ),
            )

        # The deductible affects the estimated payable amount,
        # but does not increase the policy coverage limit.
        estimated_payable = max(
            repair_cost - deductible,
            0.0,
        )

        if repair_cost > coverage_limit:
            return PolicyEvaluation(
                evaluation_id=str(uuid4()),
                claim_id=claim.claim_id,
                rule_id="REPAIR_COST_WITHIN_COVERAGE",
                result="REVIEW",
                explanation=(
                    f"Repair cost of {repair_cost:.2f} exceeds "
                    f"the policy coverage limit of "
                    f"{coverage_limit:.2f}."
                ),
                repair_cost=repair_cost,
                coverage_limit=coverage_limit,
                deductible=deductible,
                estimated_payable=estimated_payable,
            )

        return PolicyEvaluation(
            evaluation_id=str(uuid4()),
            claim_id=claim.claim_id,
            rule_id="REPAIR_COST_WITHIN_COVERAGE",
            result="PASS",
            explanation=(
                f"Repair cost of {repair_cost:.2f} is within "
                f"the policy coverage limit of "
                f"{coverage_limit:.2f}. "
                f"After applying the deductible of "
                f"{deductible:.2f}, the estimated payable amount "
                f"is {estimated_payable:.2f}."
            ),
            repair_cost=repair_cost,
            coverage_limit=coverage_limit,
            deductible=deductible,
            estimated_payable=estimated_payable,
        )