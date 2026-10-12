from src.evaluation.expense_consistency_service import (
    ExpenseConsistencyService,
)
from src.models.schemas import RepairEstimateDocument


def test_parts_and_labor_match_total():

    repair_estimate = RepairEstimateDocument(
        claim_id="CONS-001",
        total_estimated_cost=85000.0,
        parts_cost=55000.0,
        labor_cost=30000.0,
    )

    service = ExpenseConsistencyService()

    result = service.validate_repair_estimate(
        repair_estimate
    )

    assert result.result == "PASS"
    assert result.claim_id == "CONS-001"


def test_parts_and_labor_do_not_match_total():

    repair_estimate = RepairEstimateDocument(
        claim_id="CONS-002",
        total_estimated_cost=85000.0,
        parts_cost=55000.0,
        labor_cost=20000.0,
    )

    service = ExpenseConsistencyService()

    result = service.validate_repair_estimate(
        repair_estimate
    )

    assert result.result == "REVIEW"
    assert "do not match" in result.explanation.lower()


def test_missing_parts_cost_requires_review():

    repair_estimate = RepairEstimateDocument(
        claim_id="CONS-003",
        total_estimated_cost=85000.0,
        parts_cost=None,
        labor_cost=30000.0,
    )

    service = ExpenseConsistencyService()

    result = service.validate_repair_estimate(
        repair_estimate
    )

    assert result.result == "REVIEW"
    assert "parts cost" in result.explanation.lower()


def test_missing_labor_cost_requires_review():

    repair_estimate = RepairEstimateDocument(
        claim_id="CONS-004",
        total_estimated_cost=85000.0,
        parts_cost=55000.0,
        labor_cost=None,
    )

    service = ExpenseConsistencyService()

    result = service.validate_repair_estimate(
        repair_estimate
    )

    assert result.result == "REVIEW"
    assert "labor cost" in result.explanation.lower()


def test_missing_total_cost_requires_review():

    repair_estimate = RepairEstimateDocument(
        claim_id="CONS-005",
        total_estimated_cost=None,
        parts_cost=55000.0,
        labor_cost=30000.0,
    )

    service = ExpenseConsistencyService()

    result = service.validate_repair_estimate(
        repair_estimate
    )

    assert result.result == "REVIEW"
    assert "total repair cost" in result.explanation.lower()