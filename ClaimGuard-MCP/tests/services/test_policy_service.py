from src.db.schema import initialize_database
from src.models.schemas import PolicyEvaluation
from src.services.policy_service import PolicyService


def test_save_and_get_policy_evaluation():
    initialize_database()

    service = PolicyService()

    evaluation = PolicyEvaluation(
        evaluation_id="EVAL-001",
        claim_id="TEST-001",
        rule_id="REPORT-WINDOW-001",
        result="PASS",
        explanation="Claim was reported within the allowed reporting window.",
    )

    service.save_evaluation(evaluation)

    results = service.get_claim_evaluations("TEST-001")

    assert len(results) == 1
    assert results[0].evaluation_id == "EVAL-001"
    assert results[0].claim_id == "TEST-001"
    assert results[0].rule_id == "REPORT-WINDOW-001"
    assert results[0].result == "PASS"