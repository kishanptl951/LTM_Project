from datetime import date

from src.models.schemas import Claim
from src.services.claim_service import ClaimService


def test_claim_service_persists_vehicle_registration():
    service = ClaimService()

    claim = Claim(
        claim_id="TEST-VEHICLE-001",
        policy_number="POL-001",
        claimant_name="Test User",
        claim_type="VEHICLE",
        incident_date=date(2026, 1, 10),
        reported_date=date(2026, 1, 11),
        vehicle_registration="GJ01AB1234",
    )

    service.create_claim(claim)

    stored_claim = service.get_claim("TEST-VEHICLE-001")

    assert stored_claim is not None
    assert stored_claim.vehicle_registration == "GJ01AB1234"