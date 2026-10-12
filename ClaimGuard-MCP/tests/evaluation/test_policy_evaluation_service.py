from src.models.schemas import Claim, PolicyDocument
from src.evaluation.policy_evaluation_service import PolicyEvaluationService


def test_policy_evaluation_passes():
    claim = Claim(
        claim_id="TEST-POLICY-001",
        policy_number="POL-2026-001",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date="2026-09-05",
        reported_date="2026-09-06",
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-2026-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive",
        policy_start_date="2026-01-01",
        policy_end_date="2026-12-31",
        deductible=10000.0,
        coverage_limit=500000.0,
    )

    service = PolicyEvaluationService()

    results = service.evaluate_claim(
        claim=claim,
        policy=policy,
    )

    assert len(results) == 3

    assert results[0].rule_id == "POLICY_PERIOD"
    assert results[0].result == "PASS"

    assert results[1].rule_id == "POLICY_NUMBER_MATCH"
    assert results[1].result == "PASS"

    assert results[2].rule_id == "VEHICLE_REGISTRATION_MATCH"
    assert results[2].result == "PASS"