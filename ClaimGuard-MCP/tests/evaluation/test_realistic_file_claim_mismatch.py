from pathlib import Path

import fitz

from src.config import settings
from src.extraction.structured_extraction_service import (
    StructuredExtractionService,
)
from src.extraction.document_mapper_service import (
    DocumentMapperService,
)
from src.models.schemas import Claim
from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)


def create_pdf(file_path: Path, content: str) -> None:
    document = fitz.open()

    page = document.new_page()

    page.insert_textbox(
        fitz.Rect(50, 50, 550, 750),
        content,
        fontsize=11,
    )

    document.save(file_path)
    document.close()


def test_realistic_claim_package_detects_vehicle_mismatch(
    tmp_path,
):
    # ---------------------------------------------------------
    # Step 1: Use isolated temporary database
    # ---------------------------------------------------------

    original_database_path = settings.database_path

    settings.database_path = str(
        tmp_path / "test_claimguard_mismatch.duckdb"
    )

    from src.db.schema import initialize_database

    initialize_database()

    # ---------------------------------------------------------
    # Step 2: Create realistic policy document
    # ---------------------------------------------------------

    policy_pdf = tmp_path / "policy.pdf"

    create_pdf(
        policy_pdf,
        """
        MOTOR INSURANCE POLICY

        Policy Number: POL-2026-600

        Policy Holder: Rahul Sharma

        Vehicle Registration: TS09AB1234

        Coverage Type: Comprehensive

        Policy Start Date: 2026-01-01

        Policy End Date: 2026-12-31

        Coverage Limit: 100000

        Deductible: 10000
        """,
    )

    # ---------------------------------------------------------
    # Step 3: Create claim form
    # ---------------------------------------------------------

    claim_pdf = tmp_path / "claim_form.pdf"

    create_pdf(
        claim_pdf,
        """
        INSURANCE CLAIM FORM

        Claim ID: CLM-600

        Policy Number: POL-2026-600

        Claimant Name: Rahul Sharma

        Claim Type: Motor Vehicle Accident

        Incident Date: 2026-09-05

        Reported Date: 2026-09-06

        Vehicle Registration: TS09AB1234
        """,
    )

    # ---------------------------------------------------------
    # Step 4: Create police report with mismatch
    # ---------------------------------------------------------

    police_pdf = tmp_path / "police_report.pdf"

    create_pdf(
        police_pdf,
        """
        POLICE ACCIDENT REPORT

        Police Report Number: FIR-600

        Claim ID: CLM-600

        Policy Number: POL-2026-600

        Incident Date: 2026-09-05

        Vehicle Registration: TS09XY9999
        """,
    )

    # ---------------------------------------------------------
    # Step 5: Extract documents
    # ---------------------------------------------------------

    extraction_service = StructuredExtractionService()

    policy_structured = (
        extraction_service.process_document(
            file_path=str(policy_pdf),
            claim_id="CLM-600",
            document_id="DOC-POLICY-600",
        )
    )

    claim_structured = (
        extraction_service.process_document(
            file_path=str(claim_pdf),
            claim_id="CLM-600",
            document_id="DOC-CLAIM-600",
        )
    )

    police_structured = (
        extraction_service.process_document(
            file_path=str(police_pdf),
            claim_id="CLM-600",
            document_id="DOC-POLICE-600",
        )
    )

    # ---------------------------------------------------------
    # Step 6: Verify extraction
    # ---------------------------------------------------------

    assert (
        policy_structured.extracted_data[
            "vehicle_registration"
        ]
        == "TS09AB1234"
    )

    assert (
        claim_structured.extracted_data[
            "vehicle_registration"
        ]
        == "TS09AB1234"
    )

    assert (
        police_structured.extracted_data[
            "vehicle_registration"
        ]
        == "TS09XY9999"
    )

    # ---------------------------------------------------------
    # Step 7: Map structured documents
    # ---------------------------------------------------------

    mapper = DocumentMapperService()

    policy = mapper.map_document(
        policy_structured
    )

    claim_form = mapper.map_document(
        claim_structured
    )

    police_report = mapper.map_document(
        police_structured
    )

    # ---------------------------------------------------------
    # Step 8: Build claim
    # ---------------------------------------------------------

    claim = Claim(
        claim_id="CLM-600",
        policy_number="POL-2026-600",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date=claim_form.incident_date,
        reported_date=claim_form.reported_date,
        vehicle_registration=(
            claim_form.vehicle_registration
        ),
    )

    # ---------------------------------------------------------
    # Step 9: Run evaluation pipeline
    # ---------------------------------------------------------

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
    )

    # ---------------------------------------------------------
    # Step 10: Verify final result
    # ---------------------------------------------------------

    assert assessment.overall_result in {"FAIL", "REVIEW"}

    # Print actual invariant results so we can verify
    # the invariant ID and explanation used by production code.

    print("\n=== INVARIANT RESULTS ===")

    for result in assessment.invariant_results:
        print(
            f"ID={result.invariant_id} | "
            f"RESULT={result.result} | "
            f"EXPLANATION={result.explanation}"
        )

    # At least one invariant must detect the mismatch.

    mismatch_results = [
        result
        for result in assessment.invariant_results
        if result.result == "FAIL"
    ]

    assert len(mismatch_results) == 1

    # Verify that the failure actually refers to
    # both vehicle registration values.

    assert (
        "TS09AB1234"
        in mismatch_results[0].explanation
    )

    assert (
        "TS09XY9999"
        in mismatch_results[0].explanation
    )

    # ---------------------------------------------------------
    # Step 11: Restore database setting
    # ---------------------------------------------------------

    settings.database_path = original_database_path