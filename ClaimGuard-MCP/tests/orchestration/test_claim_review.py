from datetime import date

from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    PolicyDocument,
    PoliceReportDocument,
)


def test_vehicle_mismatch_returns_review():

    claim = Claim(
        claim_id="CLM-REVIEW-001",
        policy_number="POL-REAL-001",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date=date(2026, 9, 5),
        reported_date=date(2026, 9, 6),
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-REAL-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive Motor Insurance",
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
        deductible=5000,
        coverage_limit=500000,
    )

    claim_form = ClaimFormDocument(
        claim_id="CLM-REVIEW-001",
        policy_number="POL-REAL-001",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date=date(2026, 9, 5),
        reported_date=date(2026, 9, 6),
        incident_location="Hyderabad",
        incident_description=(
            "The insured vehicle was involved in a road accident. "
            "The front bumper and headlights were damaged."
        ),
        vehicle_registration="TS09AB1234",
    )

    # Deliberately incorrect vehicle registration.
    police_report = PoliceReportDocument(
        report_number="PR-REVIEW-001",
        claim_id="CLM-REVIEW-001",
        policy_number="POL-REAL-001",
        incident_date=date(2026, 9, 5),
        incident_time="18:30",
        incident_location="Hyderabad",
        police_station="Banjara Hills Police Station",
        officer_name="Arun Kumar",
        incident_description=(
            "The insured vehicle was involved in a road accident."
        ),
        vehicle_registration="TS09XY9999",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
    )

    assert assessment.overall_result in {"FAIL", "REVIEW"}

    police_vehicle_result = next(
        result
        for result in assessment.invariant_results
        if result.invariant_id
        == "VEHICLE_REGISTRATION_POLICE_REPORT_CONSISTENCY"
    )

    assert police_vehicle_result.result == "FAIL"
    assert police_vehicle_result.severity == "HIGH"