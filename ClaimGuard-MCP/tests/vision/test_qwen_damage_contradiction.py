from datetime import date
from src.config import settings
from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    PolicyDocument,
)
from src.vision.vision_extraction_service import (
    VisionExtractionService,
)


VISION_API_URL = settings.vision_api_url

IMAGE_PATH = (
    r"C:\Users\T9934\Downloads\car_damage.jpg"
)


def test_qwen_vision_detects_damage_contradiction():

    claim = Claim(
        claim_id="QWEN-DAMAGE-002",
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
        policy_start_date=date(2026, 1, 1),
        policy_end_date=date(2026, 12, 31),
    )

    claim_form = ClaimFormDocument(
        claim_id="QWEN-DAMAGE-002",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        incident_description=(
            "The vehicle sustained damage to the "
            "rear bumper."
        ),
    )

    vision_service = VisionExtractionService(
        vision_api_url=VISION_API_URL
    )

    damage_photo = vision_service.extract_damage(
        IMAGE_PATH,
        claim_id="QWEN-DAMAGE-002",
    )

    assert damage_photo.damage_area is not None

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert len(assessment.damage_results) == 1

    damage_result = assessment.damage_results[0]

    assert damage_result.invariant_id == (
        "DAMAGE_AREA_CONSISTENCY"
    )

    assert damage_result.result == "REVIEW"

    assert assessment.overall_result == "REVIEW"