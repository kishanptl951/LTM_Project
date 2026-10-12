from pathlib import Path

import fitz

from src.extraction.structured_extraction_service import (
    StructuredExtractionService,
)
from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.models.schemas import Claim


def create_pdf(path: Path, content: str) -> None:
    document = fitz.open()
    page = document.new_page()

    page.insert_text(
        (50, 50),
        content,
        fontsize=10,
    )

    document.save(path)
    document.close()


def clean_test_data() -> None:
    from src.db.session import get_db_connection

    with get_db_connection() as conn:

        for table in [
            "invariant_results",
            "policy_evaluations",
            "extracted_evidence",
            "documents",
            "claims",
        ]:
            conn.execute(
                f"""
                DELETE FROM {table}
                WHERE claim_id = 'CLM-300'
                """
            )


def test_full_claim_assessment_with_mismatch(tmp_path):

    clean_test_data()

    claim_id = "CLM-300"

    claim_form_path = tmp_path / "claim_form.pdf"
    policy_path = tmp_path / "policy.pdf"
    police_report_path = tmp_path / "police_report.pdf"

    # ---------------------------------------------------------
    # Claim Form
    # ---------------------------------------------------------
    create_pdf(
        claim_form_path,
        """
MOTOR VEHICLE INSURANCE CLAIM FORM

Claim ID: CLM-300
Policy Number: POL-2026-300
Claimant Name: Rahul Sharma
Claim Type: Motor Vehicle Accident

Incident Date: 2026-09-05
Reported Date: 2026-09-06

Vehicle Registration: TS09AB1234
Vehicle Make: Toyota
Vehicle Model: Corolla

Estimated Repair Cost: INR 85,000
""",
    )

    # ---------------------------------------------------------
    # Policy
    # ---------------------------------------------------------
    create_pdf(
        policy_path,
        """
MOTOR INSURANCE POLICY

Policy Number: POL-2026-300
Claimant Name: Rahul Sharma

Vehicle Registration: TS09AB1234
Vehicle Make: Toyota
Vehicle Model: Corolla

Policy Start Date: 2026-01-01
Policy End Date: 2026-12-31
""",
    )

    # ---------------------------------------------------------
    # Police Report
    #
    # Deliberate mismatch:
    # TS09AB1234 != TS09XY5678
    # ---------------------------------------------------------
    create_pdf(
        police_report_path,
        """
POLICE ACCIDENT REPORT

Police Report Number: HYD-2026-300

Claim ID: CLM-300

Vehicle Registration: TS09XY5678

Incident Date: 2026-09-05

Location: Hyderabad, Telangana
""",
    )

    # ---------------------------------------------------------
    # Step 1: Extract and map documents
    # ---------------------------------------------------------
    structured_pipeline = StructuredExtractionService()

    claim_form = structured_pipeline.process_and_map_document(
        file_path=str(claim_form_path),
        claim_id=claim_id,
        document_id="TEST-CLAIM-FORM-300",
    )

    policy = structured_pipeline.process_and_map_document(
        file_path=str(policy_path),
        claim_id=claim_id,
        document_id="TEST-POLICY-300",
    )

    police_report = structured_pipeline.process_and_map_document(
        file_path=str(police_report_path),
        claim_id=claim_id,
        document_id="TEST-POLICE-REPORT-300",
    )

    # ---------------------------------------------------------
    # Step 2: Verify mapped claim-form data
    # ---------------------------------------------------------
    assert claim_form.claim_id == "CLM-300"
    assert claim_form.policy_number == "POL-2026-300"
    assert claim_form.claimant_name == "Rahul Sharma"
    assert claim_form.claim_type == "Motor Vehicle Accident"
    assert str(claim_form.incident_date) == "2026-09-05"
    assert str(claim_form.reported_date) == "2026-09-06"
    assert claim_form.vehicle_registration == "TS09AB1234"

    # ---------------------------------------------------------
    # Step 3: Verify mapped policy data
    # ---------------------------------------------------------
    assert policy.policy_number == "POL-2026-300"
    assert policy.policy_holder == "Rahul Sharma"
    assert policy.vehicle_registration == "TS09AB1234"
    assert str(policy.policy_start_date) == "2026-01-01"
    assert str(policy.policy_end_date) == "2026-12-31"

    # ---------------------------------------------------------
    # Step 4: Verify mapped police-report data
    # ---------------------------------------------------------
    assert police_report.report_number == "HYD-2026-300"
    assert police_report.claim_id == "CLM-300"
    assert police_report.vehicle_registration == "TS09XY5678"
    assert str(police_report.incident_date) == "2026-09-05"

    # ---------------------------------------------------------
    # Step 5: Build the claim from mapped data
    # ---------------------------------------------------------
    claim = Claim(
        claim_id=claim_form.claim_id,
        policy_number=claim_form.policy_number or "",
        claimant_name=claim_form.claimant_name,
        claim_type=claim_form.claim_type,
        incident_date=claim_form.incident_date,
        reported_date=claim_form.reported_date,
        vehicle_registration=claim_form.vehicle_registration,
    )

    # ---------------------------------------------------------
    # Step 6: Run complete claim evaluation
    # ---------------------------------------------------------
    evaluation_pipeline = ClaimEvaluationPipeline()

    assessment = evaluation_pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
    )
    # ---------------------------------------------------------
    # Step 7: Verify final assessment
    # ---------------------------------------------------------

    # The vehicle mismatch should require review.
    assert assessment.overall_result in {"FAIL", "REVIEW"}

    # The assessment should contain reasons.
    assert len(assessment.reasons) > 0

    # Motor claims require these documents.
    assert "CLAIM_FORM" in assessment.required_documents
    assert "POLICY" in assessment.required_documents
    assert "DAMAGE_PHOTO" in assessment.required_documents

    # Damage photo is intentionally not supplied.
    assert "DAMAGE_PHOTO" in assessment.missing_documents

    # ---------------------------------------------------------
    # Verify that the vehicle mismatch was captured
    # ---------------------------------------------------------
    print("\nASSESSMENT REASONS:")

    for reason in assessment.reasons:
        print(f" - {reason}")

    assert any(
        "TS09AB1234" in reason
        and "TS09XY5678" in reason
        for reason in assessment.reasons
    )