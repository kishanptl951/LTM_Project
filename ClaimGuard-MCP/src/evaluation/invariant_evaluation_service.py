from uuid import uuid4

from src.models.schemas import (
    ClaimFormDocument,
    InvariantResult,
    PolicyDocument,
    PoliceReportDocument,
)


def _normalize(value: str | None) -> str | None:
    """Strip whitespace and uppercase for case-insensitive comparison."""
    if value is None:
        return None
    return value.strip().upper()


class InvariantEvaluationService:

    def check_vehicle_registration(
        self,
        claim_form: ClaimFormDocument,
        policy: PolicyDocument,
    ) -> InvariantResult:

        if not claim_form.vehicle_registration:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Vehicle registration is missing from the claim form."
            )

        elif not policy.vehicle_registration:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Vehicle registration is missing from the policy document."
            )

        elif (
            _normalize(claim_form.vehicle_registration)
            == _normalize(policy.vehicle_registration)
        ):
            result = "PASS"
            severity = "LOW"
            explanation = (
                f"Vehicle registration {claim_form.vehicle_registration} "
                "matches between the claim form and policy."
            )

        else:
            result = "FAIL"
            severity = "HIGH"
            explanation = (
                f"Vehicle registration {claim_form.vehicle_registration} "
                "on the claim form does not match "
                f"{policy.vehicle_registration} on the policy."
            )

        return InvariantResult(
            result_id=str(uuid4()),
            claim_id=claim_form.claim_id,
            invariant_id="VEHICLE_REGISTRATION_CONSISTENCY",
            result=result,
            severity=severity,
            explanation=explanation,
        )

    def check_vehicle_registration_against_police_report(
        self,
        claim_form: ClaimFormDocument,
        police_report: PoliceReportDocument,
    ) -> InvariantResult:

        claim_form_vehicle = claim_form.vehicle_registration
        police_report_vehicle = police_report.vehicle_registration

        if not claim_form_vehicle:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Vehicle registration is missing from the claim form."
            )

        elif not police_report_vehicle:
            # Police-report vehicle registration is optional.
            # Do not penalize the claim when it is absent.
            result = "PASS"
            severity = "LOW"
            explanation = (
                "Vehicle registration is not available in the police report; "
                "police-report vehicle consistency check was skipped."
            )

        elif _normalize(claim_form_vehicle) == _normalize(police_report_vehicle):
            result = "PASS"
            severity = "LOW"
            explanation = (
                f"Vehicle registration {claim_form_vehicle} "
                "matches between the claim form and police report."
            )

        else:
            result = "FAIL"
            severity = "HIGH"
            explanation = (
                f"Vehicle registration {claim_form_vehicle} "
                "on the claim form does not match "
                f"{police_report_vehicle} on the police report."
            )

        return InvariantResult(
            result_id=str(uuid4()),
            claim_id=claim_form.claim_id,
            invariant_id="VEHICLE_REGISTRATION_POLICE_REPORT_CONSISTENCY",
            result=result,
            severity=severity,
            explanation=explanation,
        )

    def check_policy_number(
        self,
        claim_form: ClaimFormDocument,
        policy: PolicyDocument,
    ) -> InvariantResult:

        if not claim_form.policy_number:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Policy number is missing from the claim form."
            )

        elif not policy.policy_number:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Policy number is missing from the policy document."
            )

        elif (
            _normalize(claim_form.policy_number)
            == _normalize(policy.policy_number)
        ):
            result = "PASS"
            severity = "LOW"
            explanation = (
                f"Policy number {claim_form.policy_number} "
                "matches between the claim form and policy."
            )

        else:
            result = "FAIL"
            severity = "HIGH"
            explanation = (
                f"Policy number {claim_form.policy_number} "
                "on the claim form does not match "
                f"{policy.policy_number} on the policy."
            )

        return InvariantResult(
            result_id=str(uuid4()),
            claim_id=claim_form.claim_id,
            invariant_id="POLICY_NUMBER_CONSISTENCY",
            result=result,
            severity=severity,
            explanation=explanation,
        )

    def check_incident_date(
        self,
        claim_form: ClaimFormDocument,
        police_report: PoliceReportDocument,
    ) -> InvariantResult:

        if claim_form.incident_date is None:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Incident date is missing from the claim form."
            )

        elif police_report.incident_date is None:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Incident date is missing from the police report."
            )

        elif claim_form.incident_date == police_report.incident_date:
            result = "PASS"
            severity = "LOW"
            explanation = (
                f"Incident date {claim_form.incident_date} "
                "matches between the claim form and police report."
            )

        else:
            result = "FAIL"
            severity = "HIGH"
            explanation = (
                f"Incident date {claim_form.incident_date} "
                "on the claim form does not match "
                f"{police_report.incident_date} on the police report."
            )

        return InvariantResult(
            result_id=str(uuid4()),
            claim_id=claim_form.claim_id,
            invariant_id="INCIDENT_DATE_CONSISTENCY",
            result=result,
            severity=severity,
            explanation=explanation,
        )

    def check_claimant_name(
        self,
        claim_form: ClaimFormDocument,
        policy: PolicyDocument,
    ) -> InvariantResult:

        if not claim_form.claimant_name:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Claimant name is missing from the claim form."
            )

        elif not policy.policy_holder:
            result = "REVIEW"
            severity = "MEDIUM"
            explanation = (
                "Policy holder name is missing from the policy document."
            )

        elif (
            claim_form.claimant_name.strip().lower()
            == policy.policy_holder.strip().lower()
        ):
            result = "PASS"
            severity = "LOW"
            explanation = (
                f"Claimant name {claim_form.claimant_name} "
                "matches the policy holder."
            )

        else:
            result = "FAIL"
            severity = "HIGH"
            explanation = (
                f"Claimant name {claim_form.claimant_name} "
                "on the claim form does not match "
                f"{policy.policy_holder} on the policy."
            )

        return InvariantResult(
            result_id=str(uuid4()),
            claim_id=claim_form.claim_id,
            invariant_id="CLAIMANT_NAME_CONSISTENCY",
            result=result,
            severity=severity,
            explanation=explanation,
        )