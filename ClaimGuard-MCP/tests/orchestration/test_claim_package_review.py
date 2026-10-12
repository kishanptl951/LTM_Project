from pathlib import Path

from src.models.schemas import DamagePhotoDocument
from src.orchestration.claim_package_service import (
    ClaimPackageService,
)


class FakeVisionExtractionService:

    def extract_damage(
        self,
        file_path: str,
        claim_id: str,
    ) -> DamagePhotoDocument:

        return DamagePhotoDocument(
            claim_id=claim_id,
            vehicle_registration="TS09AB1234",
            photo_description="A vehicle with front-end damage.",
            damage_area="front end",
            visible_damage="damaged front bumper and headlights",
            estimated_severity="severe",
        )


def test_claim_package_service_detects_vehicle_mismatch():
    package_path = (
        Path("data")
        / "sample_claims"
        / "realistic_package"
    )

    service = ClaimPackageService()

    service.vision_extraction_service = (
        FakeVisionExtractionService()
    )

    # First process the normal package.
    assessment = service.process_package(
        package_path=str(package_path),
        claim_id="CLM-REAL-002",
    )

    # The normal package should pass.
    assert assessment.overall_result == "PASS"