from datetime import date

from src.evaluation.invariant_evaluation_service import (
    InvariantEvaluationService,
)

from src.models.schemas import (
    ClaimFormDocument,
    PolicyDocument,
    PoliceReportDocument,
)


def test_vehicle_registration_matches():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-001",
        policy_number="POL-2026-001",
        claimant_name="Rahul Sharma",
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-2026-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
    )

    service = InvariantEvaluationService()

    result = service.check_vehicle_registration(
        claim_form=claim_form,
        policy=policy,
    )

    assert result.claim_id == "TEST-INVARIANT-001"
    assert result.invariant_id == "VEHICLE_REGISTRATION_CONSISTENCY"
    assert result.result == "PASS"
    assert result.severity == "LOW"


def test_vehicle_registration_mismatch():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-002",
        policy_number="POL-2026-001",
        claimant_name="Rahul Sharma",
        vehicle_registration="TS09XY9999",
    )

    policy = PolicyDocument(
        policy_number="POL-2026-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
    )

    service = InvariantEvaluationService()

    result = service.check_vehicle_registration(
        claim_form=claim_form,
        policy=policy,
    )

    assert result.claim_id == "TEST-INVARIANT-002"
    assert result.invariant_id == "VEHICLE_REGISTRATION_CONSISTENCY"
    assert result.result == "FAIL"
    assert result.severity == "HIGH"


def test_check_policy_number_matching():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-003",
        policy_number="POL-001",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
    )

    service = InvariantEvaluationService()

    result = service.check_policy_number(
        claim_form=claim_form,
        policy=policy,
    )

    assert result.result == "PASS"
    assert result.severity == "LOW"
    assert result.invariant_id == "POLICY_NUMBER_CONSISTENCY"


def test_check_policy_number_mismatch():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-004",
        policy_number="POL-999",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
    )

    service = InvariantEvaluationService()

    result = service.check_policy_number(
        claim_form=claim_form,
        policy=policy,
    )

    assert result.result == "FAIL"
    assert result.severity == "HIGH"
    assert result.invariant_id == "POLICY_NUMBER_CONSISTENCY"
    assert "does not match" in result.explanation


def test_check_incident_date_matching():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-005",
        incident_date=date(2026, 9, 5),
    )

    police_report = PoliceReportDocument(
        claim_id="TEST-INVARIANT-005",
        incident_date=date(2026, 9, 5),
    )

    service = InvariantEvaluationService()

    result = service.check_incident_date(
        claim_form=claim_form,
        police_report=police_report,
    )

    assert result.result == "PASS"
    assert result.severity == "LOW"
    assert result.invariant_id == "INCIDENT_DATE_CONSISTENCY"


def test_check_incident_date_mismatch():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-006",
        incident_date=date(2026, 9, 5),
    )

    police_report = PoliceReportDocument(
        claim_id="TEST-INVARIANT-006",
        incident_date=date(2026, 9, 6),
    )

    service = InvariantEvaluationService()

    result = service.check_incident_date(
        claim_form=claim_form,
        police_report=police_report,
    )

    assert result.result == "FAIL"
    assert result.severity == "HIGH"
    assert result.invariant_id == "INCIDENT_DATE_CONSISTENCY"
    assert "does not match" in result.explanation


def test_check_claimant_name_matching():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-007",
        claimant_name="Rahul Sharma",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="rahul sharma",
    )

    service = InvariantEvaluationService()

    result = service.check_claimant_name(
        claim_form=claim_form,
        policy=policy,
    )

    assert result.result == "PASS"
    assert result.severity == "LOW"
    assert result.invariant_id == "CLAIMANT_NAME_CONSISTENCY"


def test_check_claimant_name_mismatch():
    claim_form = ClaimFormDocument(
        claim_id="TEST-INVARIANT-008",
        claimant_name="Rahul Sharma",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Amit Patel",
    )

    service = InvariantEvaluationService()

    result = service.check_claimant_name(
        claim_form=claim_form,
        policy=policy,
    )

    assert result.result == "FAIL"
    assert result.severity == "HIGH"
    assert result.invariant_id == "CLAIMANT_NAME_CONSISTENCY"
    assert "does not match" in result.explanation