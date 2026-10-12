from datetime import date

from src.evaluation.claim_assessment_service import ClaimAssessmentService
from src.models.schemas import (
    Claim,
    InvariantResult,
    PolicyEvaluation,
)


def test_claim_assessment_pass():

    claim = Claim(
        claim_id="TEST-ASSESS-001",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    policy_results = [
        PolicyEvaluation(
            evaluation_id="EVAL-ASSESS-001",
            claim_id=claim.claim_id,
            rule_id="POLICY_PERIOD",
            result="PASS",
            explanation="Incident is within policy period.",
        )
    ]

    invariant_results = [
        InvariantResult(
            result_id="INV-ASSESS-001",
            claim_id=claim.claim_id,
            invariant_id="VEHICLE_REGISTRATION_CONSISTENCY",
            result="PASS",
            severity="LOW",
            explanation="Vehicle registration matches.",
        )
    ]

    service = ClaimAssessmentService()

    assessment = service.assess_claim(
        claim=claim,
        policy_results=policy_results,
        invariant_results=invariant_results,
        evidence_count=2,
    )

    assert assessment.overall_result == "PASS"
    assert assessment.claim_id == "TEST-ASSESS-001"
    assert assessment.evidence_count == 2
    assert assessment.reasons == []


def test_claim_assessment_fail_on_failure():

    claim = Claim(
        claim_id="TEST-ASSESS-002",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    policy_results = [
        PolicyEvaluation(
            evaluation_id="EVAL-ASSESS-002",
            claim_id=claim.claim_id,
            rule_id="VEHICLE_REGISTRATION_MATCH",
            result="FAIL",
            explanation="Vehicle registration does not match.",
        )
    ]

    invariant_results = []

    service = ClaimAssessmentService()

    assessment = service.assess_claim(
        claim=claim,
        policy_results=policy_results,
        invariant_results=invariant_results,
    )

    assert assessment.overall_result == "FAIL"
    assert len(assessment.reasons) == 1
    assert "does not match" in assessment.reasons[0]


def test_claim_assessment_review_on_review_result():

    claim = Claim(
        claim_id="TEST-ASSESS-003",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    policy_results = [
        PolicyEvaluation(
            evaluation_id="EVAL-ASSESS-003",
            claim_id=claim.claim_id,
            rule_id="POLICY_PERIOD",
            result="REVIEW",
            explanation="Incident date needs verification.",
        )
    ]

    service = ClaimAssessmentService()

    assessment = service.assess_claim(
        claim=claim,
        policy_results=policy_results,
        invariant_results=[],
    )

    assert assessment.overall_result == "REVIEW"
    assert len(assessment.reasons) == 1


def test_claim_assessment_review_on_missing_documents():

    claim = Claim(
        claim_id="TEST-ASSESS-004",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    service = ClaimAssessmentService()

    assessment = service.assess_claim(
        claim=claim,
        policy_results=[],
        invariant_results=[],
        missing_documents=["POLICE_REPORT"],
    )

    assert assessment.overall_result == "REVIEW"
    assert any("missing: POLICE_REPORT" in r for r in assessment.reasons)