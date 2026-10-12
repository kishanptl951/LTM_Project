from src.evaluation.damage_consistency_service import (
    DamageConsistencyService,
)
from src.models.schemas import (
    ClaimFormDocument,
    DamagePhotoDocument,
)


def test_photo_damage_matches_claim():

    claim_form = ClaimFormDocument(
        claim_id="DAMAGE-001",
        incident_description=(
            "The vehicle sustained damage to the front bumper."
        ),
    )

    damage_photo = DamagePhotoDocument(
        claim_id="DAMAGE-001",
        damage_area="front bumper",
        visible_damage="front bumper dent and scratches",
        estimated_severity="moderate",
    )

    service = DamageConsistencyService()

    result = service.compare_damage(
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert result.result == "PASS"
    assert result.claim_id == "DAMAGE-001"


def test_photo_damage_conflicts_with_claim():

    claim_form = ClaimFormDocument(
        claim_id="DAMAGE-002",
        incident_description=(
            "The vehicle sustained damage to the front bumper."
        ),
    )

    damage_photo = DamagePhotoDocument(
        claim_id="DAMAGE-002",
        damage_area="rear bumper",
        visible_damage="rear bumper dent",
        estimated_severity="moderate",
    )

    service = DamageConsistencyService()

    result = service.compare_damage(
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert result.result == "REVIEW"
    assert "damage area" in result.explanation.lower()


def test_missing_claim_description_requires_review():

    claim_form = ClaimFormDocument(
        claim_id="DAMAGE-003",
        incident_description=None,
    )

    damage_photo = DamagePhotoDocument(
        claim_id="DAMAGE-003",
        damage_area="front bumper",
        visible_damage="front bumper dent",
    )

    service = DamageConsistencyService()

    result = service.compare_damage(
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert result.result == "REVIEW"
    assert "incident description" in result.explanation.lower()


def test_missing_photo_damage_area_requires_review():

    claim_form = ClaimFormDocument(
        claim_id="DAMAGE-004",
        incident_description=(
            "The vehicle sustained damage to the front bumper."
        ),
    )

    damage_photo = DamagePhotoDocument(
        claim_id="DAMAGE-004",
        damage_area=None,
        visible_damage="visible scratches",
    )

    service = DamageConsistencyService()

    result = service.compare_damage(
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert result.result == "REVIEW"
    assert "damage area" in result.explanation.lower()