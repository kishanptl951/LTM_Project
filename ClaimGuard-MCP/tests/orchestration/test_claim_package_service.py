from pathlib import Path


from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    DamagePhotoDocument,
    PolicyDocument,
)

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
            photo_description=(
                "A vehicle with front-end damage."
            ),
            damage_area="front end",
            visible_damage=(
                "damaged front bumper and headlights"
            ),
            estimated_severity="severe",
        )


def test_claim_package_service_motor_claim():
    package_path = (
        Path("data")
        / "sample_claims"
        / "realistic_package"
    )

    service = ClaimPackageService()

    # Replace only the vision dependency for this test.
    # The real Qwen integration is tested separately.
    service.vision_extraction_service = (
        FakeVisionExtractionService()
    )

    assessment = service.process_package(
        package_path=str(package_path),
        claim_id="CLM-REAL-001",
    )

    assert assessment.claim_id == "CLM-REAL-001"

    assert assessment.overall_result == "PASS"

    assert assessment.missing_documents == []

    assert len(assessment.policy_results) > 0

    assert len(assessment.invariant_results) > 0

    assert len(assessment.expense_results) > 0

    assert len(assessment.damage_results) > 0


def test_multiple_damage_photos_not_overwritten():
    from src.evaluation.claim_evaluation_pipeline import ClaimEvaluationPipeline
    from datetime import date

    claim = Claim(claim_id="CLM-MULTI-01", policy_number="POL-123")
    policy = PolicyDocument(policy_number="POL-123", policy_start_date=date(2026, 1, 1), policy_end_date=date(2026, 12, 31))
    claim_form = ClaimFormDocument(
        claim_id="CLM-MULTI-01",
        policy_number="POL-123",
        incident_date=date(2026, 5, 1),
        incident_description="Front bumper collided and rear left door scratched",
    )

    photo_front = DamagePhotoDocument(
        claim_id="CLM-MULTI-01",
        damage_area="front bumper",
        photo_description="Front bumper damage",
    )
    photo_door = DamagePhotoDocument(
        claim_id="CLM-MULTI-01",
        damage_area="left door",
        photo_description="Left door scratch",
    )

    pipeline = ClaimEvaluationPipeline()
    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        damage_photos=[photo_front, photo_door],
    )

    # Both photos must be analyzed without overwriting
    assert len(assessment.damage_results) == 2
    assert "DAMAGE_PHOTO" in assessment.available_documents


def test_missing_policy_number_safely_handled():
    from src.evaluation.claim_evaluation_pipeline import ClaimEvaluationPipeline
    from datetime import date

    # Claim constructed without policy_number (None)
    claim = Claim(claim_id="CLM-NO-POL")
    assert claim.policy_number is None

    policy = PolicyDocument(policy_number="POL-999", policy_start_date=date(2026, 1, 1), policy_end_date=date(2026, 12, 31))
    claim_form = ClaimFormDocument(
        claim_id="CLM-NO-POL",
        policy_number=None,
        incident_date=date(2026, 5, 1),
    )

    pipeline = ClaimEvaluationPipeline()
    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
    )

    # Should safely evaluate with REVIEW for policy number rather than crashing
    assert assessment.overall_result in {"REVIEW", "FAIL"}
    pol_num_result = next(r for r in assessment.policy_results if r.rule_id == "POLICY_NUMBER_MATCH")
    assert pol_num_result.result == "REVIEW"


def test_financial_exceeding_coverage_retains_fields():
    from src.evaluation.expense_evaluation_service import ExpenseEvaluationService
    from src.models.schemas import RepairEstimateDocument

    service = ExpenseEvaluationService()
    claim = Claim(claim_id="CLM-EXP-01", policy_number="POL-1")
    policy = PolicyDocument(policy_number="POL-1", coverage_limit=100000.0, deductible=5000.0)
    repair = RepairEstimateDocument(claim_id="CLM-EXP-01", total_estimated_cost=150000.0)

    result = service.evaluate_repair_cost(claim=claim, policy=policy, repair_estimate=repair)

    assert result.result == "REVIEW"
    assert result.repair_cost == 150000.0
    assert result.coverage_limit == 100000.0
    assert result.deductible == 5000.0
    assert result.estimated_payable is not None


def test_smart_image_classification_routes_scanned_image_to_structured_document(tmp_path):
    from src.ingestion.document_classifier_service import DocumentClassifierService

    class MockExtractor:

        def extract_text_from_image(self, file_path):
            if "police" in str(file_path):
                return (
                    "Police Report\nFIR Number: FIR-777\nPolice Station: Station 1\nIncident Date: 2026-05-01"
                )
            return ""

        def extract_text_from_pdf(self, file_path):
            if "claim_form" in str(file_path):
                return (
                    "Insurance Claim Form\nClaim ID: CLM-SMART-01\nPolicy Number: POL-1\nIncident Date: 2026-05-01\nClaimant Name: John Doe\nClaim Type: ACCIDENT"
                )
            if "policy" in str(file_path):
                return (
                    "Insurance Policy\nPolicy Number: POL-1\nPolicy Start Date: 2026-01-01\nPolicy End Date: 2026-12-31\nCoverage: Comprehensive\nPremium: 10000"
                )
            return ""

    extractor = MockExtractor()
    classifier = DocumentClassifierService(extraction_service=extractor)

    service = ClaimPackageService(classifier_service=classifier)
    service.structured_extraction_service.extraction_service = extractor
    service.vision_extraction_service = FakeVisionExtractionService()

    # Create dummy claim package in tmp_path
    (tmp_path / "claim_form.pdf").write_text("dummy")
    (tmp_path / "policy.pdf").write_text("dummy")
    (tmp_path / "police_report.png").write_text("dummy")  # Scanned image!
    (tmp_path / "damage.jpg").write_text("dummy")  # Real damage photo

    assessment = service.process_package(
        package_path=str(tmp_path),
        claim_id="CLM-SMART-01",
    )

    # Scanned police report (.png) was identified as POLICE_REPORT, not lost as damage photo
    assert "POLICE_REPORT" in assessment.available_documents
    assert "DAMAGE_PHOTO" in assessment.available_documents