from datetime import date

from src.evaluation.expense_evaluation_service import (
    ExpenseEvaluationService,
)
from src.models.schemas import (
    Claim,
    PolicyDocument,
    RepairEstimateDocument,
)


def test_repair_cost_within_coverage_passes():

    claim = Claim(
        claim_id="EXP-001",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        coverage_limit=100000.0,
        deductible=10000.0,
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="EXP-001",
        policy_number="POL-001",
        total_estimated_cost=85000.0,
    )

    service = ExpenseEvaluationService()

    result = service.evaluate_repair_cost(
        claim=claim,
        policy=policy,
        repair_estimate=repair_estimate,
    )

    assert result.result == "PASS"
    assert result.claim_id == "EXP-001"


def test_repair_cost_exceeds_coverage_requires_review():

    claim = Claim(
        claim_id="EXP-002",
        policy_number="POL-001",
        incident_date=date(2026, 9, 5),
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        coverage_limit=50000.0,
        deductible=5000.0,
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="EXP-002",
        policy_number="POL-001",
        total_estimated_cost=85000.0,
    )

    service = ExpenseEvaluationService()

    result = service.evaluate_repair_cost(
        claim=claim,
        policy=policy,
        repair_estimate=repair_estimate,
    )

    assert result.result == "REVIEW"
    assert "exceeds" in result.explanation.lower()


def test_missing_repair_cost_requires_review():

    claim = Claim(
        claim_id="EXP-003",
        policy_number="POL-001",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        coverage_limit=100000.0,
        deductible=10000.0,
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="EXP-003",
        policy_number="POL-001",
        total_estimated_cost=None,
    )

    service = ExpenseEvaluationService()

    result = service.evaluate_repair_cost(
        claim=claim,
        policy=policy,
        repair_estimate=repair_estimate,
    )

    assert result.result == "REVIEW"
    assert "repair cost" in result.explanation.lower()


def test_missing_coverage_limit_requires_review():

    claim = Claim(
        claim_id="EXP-004",
        policy_number="POL-001",
    )

    policy = PolicyDocument(
        policy_number="POL-001",
        coverage_limit=None,
        deductible=10000.0,
    )

    repair_estimate = RepairEstimateDocument(
        claim_id="EXP-004",
        policy_number="POL-001",
        total_estimated_cost=85000.0,
    )

    service = ExpenseEvaluationService()

    result = service.evaluate_repair_cost(
        claim=claim,
        policy=policy,
        repair_estimate=repair_estimate,
    )

    assert result.result == "REVIEW"
    assert "coverage limit" in result.explanation.lower()