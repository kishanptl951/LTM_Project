from datetime import date

from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    PolicyDocument,
    RepairEstimateDocument,
)


def test_pipeline_includes_expense_pass_result():

    claim = Claim(
        claim_id="PIPE-EXP-001",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_limit=100000.0,
        deductible=10000.0,
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
    )

    claim_form = ClaimFormDocument(
        claim_id="PIPE-EXP-001",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="PIPE-EXP-001",
        policy_number="POL-001",
        total_estimated_cost=85000.0,
        parts_cost=55000.0,
        labor_cost=30000.0,
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        repair_estimate=repair_estimate,
    )

    assert len(assessment.expense_results) == 2

    assert (
        assessment.expense_results[0].rule_id
        == "REPAIR_COST_WITHIN_COVERAGE"
    )
    assert assessment.expense_results[0].result == "PASS"

    assert (
        assessment.expense_results[1].rule_id
        == "REPAIR_COST_COMPONENTS_MATCH_TOTAL"
    )
    assert assessment.expense_results[1].result == "PASS"

    assert assessment.overall_result == "PASS"


def test_pipeline_includes_expense_review_when_cost_exceeds_limit():

    claim = Claim(
        claim_id="PIPE-EXP-002",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        coverage_limit=50000.0,
        deductible=5000.0,
    )

    claim_form = ClaimFormDocument(
        claim_id="PIPE-EXP-002",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="PIPE-EXP-002",
        policy_number="POL-001",
        total_estimated_cost=85000.0,
        parts_cost=55000.0,
        labor_cost=30000.0,
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        repair_estimate=repair_estimate,
    )

    assert len(assessment.expense_results) == 2

    assert (
        assessment.expense_results[0].rule_id
        == "REPAIR_COST_WITHIN_COVERAGE"
    )
    assert assessment.expense_results[0].result == "REVIEW"

    assert (
        assessment.expense_results[1].rule_id
        == "REPAIR_COST_COMPONENTS_MATCH_TOTAL"
    )
    assert assessment.expense_results[1].result == "PASS"

    assert assessment.overall_result == "REVIEW"


def test_pipeline_detects_repair_cost_component_mismatch():

    claim = Claim(
        claim_id="PIPE-EXP-003",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_limit=100000.0,
        deductible=10000.0,
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
    )

    claim_form = ClaimFormDocument(
        claim_id="PIPE-EXP-003",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        vehicle_registration="TS09AB1234",
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="PIPE-EXP-003",
        policy_number="POL-001",
        total_estimated_cost=85000.0,
        parts_cost=55000.0,
        labor_cost=20000.0,
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        repair_estimate=repair_estimate,
    )

    assert len(assessment.expense_results) == 2

    assert (
        assessment.expense_results[0].result == "PASS"
    )

    assert (
        assessment.expense_results[1].rule_id
        == "REPAIR_COST_COMPONENTS_MATCH_TOTAL"
    )
    assert assessment.expense_results[1].result == "REVIEW"
    assert (
        "do not match"
        in assessment.expense_results[1].explanation.lower()
    )

    assert assessment.overall_result == "REVIEW"


def test_pipeline_works_without_repair_estimate():

    claim = Claim(
        claim_id="PIPE-EXP-004",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        policy_holder="Rahul Sharma",
        coverage_limit=100000.0,
        deductible=10000.0,
    )

    claim_form = ClaimFormDocument(
        claim_id="PIPE-EXP-004",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
    )

    assert assessment.expense_results == []