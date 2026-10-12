from datetime import date

from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    DamagePhotoDocument,
    PolicyDocument,
)


def test_pipeline_includes_damage_consistency_pass():

    claim = Claim(
        claim_id="PIPE-DAMAGE-001",
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
        claim_id="PIPE-DAMAGE-001",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        incident_description=(
            "The vehicle sustained damage to the front bumper."
        ),
    )

    damage_photo = DamagePhotoDocument(
        claim_id="PIPE-DAMAGE-001",
        damage_area="front bumper",
        visible_damage="front bumper dent and scratches",
        estimated_severity="moderate",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert len(assessment.damage_results) == 1
    assert assessment.damage_results[0].result == "PASS"
    assert (
        assessment.damage_results[0].invariant_id
        == "DAMAGE_AREA_CONSISTENCY"
    )


def test_pipeline_includes_damage_consistency_review():

    claim = Claim(
        claim_id="PIPE-DAMAGE-002",
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
        claim_id="PIPE-DAMAGE-002",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        incident_description=(
            "The vehicle sustained damage to the front bumper."
        ),
    )

    damage_photo = DamagePhotoDocument(
        claim_id="PIPE-DAMAGE-002",
        damage_area="rear bumper",
        visible_damage="rear bumper dent",
        estimated_severity="moderate",
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        damage_photo=damage_photo,
    )

    assert len(assessment.damage_results) == 1
    assert assessment.damage_results[0].result == "REVIEW"
    assert (
        assessment.damage_results[0].invariant_id
        == "DAMAGE_AREA_CONSISTENCY"
    )
    assert assessment.overall_result == "REVIEW"


def test_pipeline_works_without_damage_photo():

    claim = Claim(
        claim_id="PIPE-DAMAGE-003",
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
        claim_id="PIPE-DAMAGE-003",
        policy_number="POL-001",
        claimant_name="Rahul Sharma",
        claim_type="Property Damage",
        incident_date=date(2026, 9, 5),
        incident_description=(
            "The vehicle sustained damage to the front bumper."
        ),
    )

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
    )

    assert assessment.damage_results == []