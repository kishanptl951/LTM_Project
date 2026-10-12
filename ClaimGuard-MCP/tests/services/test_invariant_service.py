from src.db.schema import initialize_database
from src.models.schemas import InvariantResult
from src.services.invariant_service import InvariantService


def test_save_and_get_invariant_result():
    initialize_database()

    service = InvariantService()

    result = InvariantResult(
        result_id="INV-001",
        claim_id="TEST-001",
        invariant_id="DATE-MISMATCH-001",
        result="FAIL",
        severity="HIGH",
        explanation="Incident dates differ across submitted documents.",
    )

    service.save_result(result)

    results = service.get_claim_results("TEST-001")

    assert len(results) == 1
    assert results[0].result_id == "INV-001"
    assert results[0].claim_id == "TEST-001"
    assert results[0].invariant_id == "DATE-MISMATCH-001"
    assert results[0].result == "FAIL"
    assert results[0].severity == "HIGH"