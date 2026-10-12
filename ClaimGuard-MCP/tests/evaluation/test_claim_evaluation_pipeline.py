from datetime import date

from src.evaluation.claim_evaluation_pipeline import ClaimEvaluationPipeline
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    PolicyDocument,
    PoliceReportDocument,
    RepairEstimateDocument,
)


def test_claim_evaluation_pipeline_pass():

    claim = Claim(
        claim_id="TEST-PIPELINE-001",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive",
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
    )

    claim_form = ClaimFormDocument(
        claim_id="TEST-PIPELINE-001",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    police_report = PoliceReportDocument(
        claim_id="TEST-PIPELINE-001",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
        evidence_count=5,
    )

    assert assessment.claim_id == "TEST-PIPELINE-001"
    assert assessment.overall_result == "PASS"
    assert assessment.evidence_count == 5
    assert len(assessment.policy_results) == 3

    # Vehicle registration + policy number + claimant name + incident date
    assert len(assessment.invariant_results) == 4

    assert assessment.reasons == []


def test_claim_evaluation_pipeline_review_on_vehicle_mismatch():

    claim = Claim(
        claim_id="TEST-PIPELINE-002",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB9999",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive",
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
    )

    claim_form = ClaimFormDocument(
        claim_id="TEST-PIPELINE-002",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB9999",
    )

    police_report = PoliceReportDocument(
        claim_id="TEST-PIPELINE-002",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
    )

    assert assessment.claim_id == "TEST-PIPELINE-002"
    assert assessment.overall_result in {"FAIL", "REVIEW"}

    # Vehicle mismatch creates one policy failure
    # and one invariant failure.
    assert len(assessment.reasons) == 2


def test_claim_evaluation_pipeline_without_police_report():

    claim = Claim(
        claim_id="TEST-PIPELINE-003",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive",
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
    )

    claim_form = ClaimFormDocument(
        claim_id="TEST-PIPELINE-003",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        evidence_count=3,
    )

    assert assessment.claim_id == "TEST-PIPELINE-003"
    assert assessment.overall_result == "PASS"

    # Without police report:
    # Vehicle registration + policy number + claimant name
    assert len(assessment.invariant_results) == 3

    assert assessment.reasons == []


def test_claim_evaluation_pipeline_with_repair_estimate():

    claim = Claim(
        claim_id="TEST-PIPELINE-004",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive",
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
        coverage_limit=100000.0,
        deductible=5000.0,
    )

    claim_form = ClaimFormDocument(
        claim_id="TEST-PIPELINE-004",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    repair_estimate = RepairEstimateDocument(
        estimate_number="EST-001",
        claim_id="TEST-PIPELINE-004",
        policy_number="POL-001",
        vehicle_registration="TS09AB1234",
        repair_date=date(2026, 9, 6),
        workshop_name="Speedy Auto",
        total_estimated_cost=45000.0,
        parts_cost=30000.0,
        labor_cost=15000.0,
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        repair_estimate=repair_estimate,
    )

    assert assessment.claim_id == "TEST-PIPELINE-004"
    assert "REPAIR_ESTIMATE" not in assessment.missing_documents
    assert len(assessment.expense_results) == 2
    assert all(r.result == "PASS" for r in assessment.expense_results)
    assert assessment.overall_result == "PASS"