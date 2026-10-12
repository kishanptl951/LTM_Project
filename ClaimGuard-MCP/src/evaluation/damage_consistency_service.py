import re
from uuid import uuid4

from src.models.schemas import (
    ClaimFormDocument,
    DamagePhotoDocument,
    InvariantResult,
)


class DamageConsistencyService:

    def compare_damage(
        self,
        claim_form: ClaimFormDocument,
        damage_photo: DamagePhotoDocument,
    ) -> InvariantResult:

        claim_description = claim_form.incident_description
        photo_damage_area = damage_photo.damage_area

        if not claim_description:
            return InvariantResult(
                result_id=str(uuid4()),
                claim_id=claim_form.claim_id,
                invariant_id="DAMAGE_AREA_CONSISTENCY",
                result="REVIEW",
                severity="MEDIUM",
                explanation=(
                    "Incident description is missing from "
                    "the claim form."
                ),
            )

        if not photo_damage_area:
            explanation = "Damage area is missing from the damage photo observation."
            if damage_photo.photo_description and (
                "vision" in damage_photo.photo_description.lower()
                or "unavailable" in damage_photo.photo_description.lower()
            ):
                explanation = (
                    f"Damage area could not be automatically extracted from photo: "
                    f"{damage_photo.photo_description}"
                )

            return InvariantResult(
                result_id=str(uuid4()),
                claim_id=claim_form.claim_id,
                invariant_id="DAMAGE_AREA_CONSISTENCY",
                result="REVIEW",
                severity="MEDIUM",
                explanation=explanation,
            )

        normalized_description = claim_description.lower().strip()
        normalized_area = photo_damage_area.lower().strip()

        # Normalize common wording differences.
        aliases = {
            "front": [
                "front",
                "front end",
                "front-end",
                "front bumper",
                "front-bumper",
                "bumper front",
                "hood",
                "bonnet",
                "front grille",
                "front grille",
                "front headlight",
                "front headlights",
            ],
            "rear": [
                "rear",
                "rear end",
                "rear-end",
                "rear bumper",
                "rear-bumper",
                "bumper rear",
                "rear grille",
                "rear light",
                "rear lights",
                "taillight",
                "tail light",
            ],
            "left door": [
                "left door",
                "driver door",
                "driver-side door",
            ],
            "right door": [
                "right door",
                "passenger door",
                "passenger-side door",
            ],
            "hood": [
                "hood",
                "bonnet",
            ],
            "windshield": [
                "windshield",
                "windscreen",
            ],
        }

        def area_matches(
            description: str,
            photo_area: str,
        ) -> bool:

            for canonical_area, terms in aliases.items():

                photo_matches = (
                    photo_area == canonical_area
                    or photo_area in terms
                    or any(
                        term in photo_area
                        for term in terms
                    )
                )

                description_matches = any(
                    re.search(
                        rf"\b{re.escape(term)}\b",
                        description,
                    )
                    for term in terms
                )

                if photo_matches and description_matches:
                    return True

            return (
                normalized_area in normalized_description
            )

        if area_matches(
            normalized_description,
            normalized_area,
        ):
            return InvariantResult(
                result_id=str(uuid4()),
                claim_id=claim_form.claim_id,
                invariant_id="DAMAGE_AREA_CONSISTENCY",
                result="PASS",
                severity="LOW",
                explanation=(
                    f"Damage area '{photo_damage_area}' "
                    "is consistent with the claim "
                    "description."
                ),
            )

        return InvariantResult(
            result_id=str(uuid4()),
            claim_id=claim_form.claim_id,
            invariant_id="DAMAGE_AREA_CONSISTENCY",
            result="REVIEW",
            severity="MEDIUM",
            explanation=(
                f"Photo identifies damage area "
                f"'{photo_damage_area}', but the claim "
                "description does not identify the same "
                "damage area."
            ),
        )