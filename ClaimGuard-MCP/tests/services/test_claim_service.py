from src.db.schema import initialize_database
from src.models.schemas import Claim
from src.services.claim_service import ClaimService


def test_create_and_get_claim():
    initialize_database()

    service = ClaimService()

    claim = Claim(
        claim_id="TEST-001",
        policy_number="POL-TEST-001",
        claimant_name="Test User",
        claim_type="AUTO",
    )

    service.create_claim(claim)

    result = service.get_claim("TEST-001")

    assert result is not None
    assert result.claim_id == "TEST-001"
    assert result.policy_number == "POL-TEST-001"
    assert result.claimant_name == "Test User"
    assert result.claim_type == "AUTO"