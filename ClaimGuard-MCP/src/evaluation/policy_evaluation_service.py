from uuid import uuid4

from src.models.schemas import Claim, PolicyDocument, PolicyEvaluation


def _normalize(value: str | None) -> str | None:
    """Strip whitespace and uppercase for case-insensitive comparison."""
    if value is None:
        return None
    return value.strip().upper()


class PolicyEvaluationService:

    def evaluate_claim(
        self,
        claim: Claim,
        policy: PolicyDocument,
    ) -> list[PolicyEvaluation]:

        evaluations = []

        evaluations.append(
            self._check_policy_period(
                claim=claim,
                policy=policy,
            )
        )

        evaluations.append(
            self._check_policy_number(
                claim=claim,
                policy=policy,
            )
        )

        evaluations.append(
            self._check_vehicle_registration(
                claim=claim,
                policy=policy,
            )
        )

        return evaluations

    def _check_policy_period(
        self,
        claim: Claim,
        policy: PolicyDocument,
    ) -> PolicyEvaluation:

        if claim.incident_date is None:
            result = "REVIEW"
            explanation = (
                "Incident date is missing, so policy-period "
                "coverage cannot be determined."
            )

        elif policy.policy_start_date is None or policy.policy_end_date is None:
            result = "REVIEW"
            explanation = (
                "Policy start or end date is missing, so policy-period "
                "coverage cannot be determined."
            )

        elif (
            policy.policy_start_date
            <= claim.incident_date
            <= policy.policy_end_date
        ):
            result = "PASS"
            explanation = (
                f"Incident date {claim.incident_date} falls within the "
                f"policy period {policy.policy_start_date} to "
                f"{policy.policy_end_date}."
            )

        else:
            result = "FAIL"
            explanation = (
                f"Incident date {claim.incident_date} falls outside the "
                f"policy period {policy.policy_start_date} to "
                f"{policy.policy_end_date}."
            )

        return PolicyEvaluation(
            evaluation_id=str(uuid4()),
            claim_id=claim.claim_id,
            rule_id="POLICY_PERIOD",
            result=result,
            explanation=explanation,
        )

    def _check_policy_number(
        self,
        claim: Claim,
        policy: PolicyDocument,
    ) -> PolicyEvaluation:

        if not claim.policy_number:
            result = "REVIEW"
            explanation = "Claim policy number is missing."

        elif not policy.policy_number:
            result = "REVIEW"
            explanation = "Policy document policy number is missing."

        elif _normalize(claim.policy_number) == _normalize(policy.policy_number):
            result = "PASS"
            explanation = (
                f"Claim policy number {claim.policy_number} "
                "matches the policy document."
            )

        else:
            result = "FAIL"
            explanation = (
                f"Claim policy number {claim.policy_number} does not match "
                f"policy document number {policy.policy_number}."
            )

        return PolicyEvaluation(
            evaluation_id=str(uuid4()),
            claim_id=claim.claim_id,
            rule_id="POLICY_NUMBER_MATCH",
            result=result,
            explanation=explanation,
        )

    def _check_vehicle_registration(
        self,
        claim: Claim,
        policy: PolicyDocument,
    ) -> PolicyEvaluation:

        claim_vehicle = claim.vehicle_registration
        policy_vehicle = policy.vehicle_registration

        if not claim_vehicle:
            result = "REVIEW"
            explanation = "Claim vehicle registration is missing."

        elif not policy_vehicle:
            result = "REVIEW"
            explanation = "Policy vehicle registration is missing."

        elif _normalize(claim_vehicle) == _normalize(policy_vehicle):
            result = "PASS"
            explanation = (
                f"Claim vehicle registration {claim_vehicle} "
                "matches the policy document."
            )

        else:
            result = "FAIL"
            explanation = (
                f"Claim vehicle registration {claim_vehicle} does not match "
                f"policy vehicle registration {policy_vehicle}."
            )

        return PolicyEvaluation(
            evaluation_id=str(uuid4()),
            claim_id=claim.claim_id,
            rule_id="VEHICLE_REGISTRATION_MATCH",
            result=result,
            explanation=explanation,
        )