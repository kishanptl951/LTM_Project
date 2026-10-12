from pathlib import Path
import fitz

from src.config import settings
from src.extraction.structured_extraction_service import (
    StructuredExtractionService,
)
from src.extraction.document_mapper_service import (
    DocumentMapperService,
)
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    PolicyDocument,
    PoliceReportDocument,
    RepairEstimateDocument,
)
from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)


def create_pdf(
    file_path: Path,
    content: str,
) -> None:

    document = fitz.open()

    page = document.new_page()

    page.insert_textbox(
        fitz.Rect(50, 50, 550, 750),
        content,
        fontsize=11,
    )

    document.save(file_path)
    document.close()


def test_realistic_claim_package_from_actual_pdfs(
    tmp_path,
):
    # Use an isolated temporary database for this test.
    original_database_path = settings.database_path
    settings.database_path = str(
        tmp_path / "test_claimguard.duckdb"
    )
    from src.db.schema import initialize_database

    initialize_database()

    # ---------------------------------------------------------
    # Step 1: Create realistic claim documents
    # ---------------------------------------------------------

    policy_pdf = tmp_path / "policy.pdf"

    create_pdf(
        policy_pdf,
        """
        MOTOR INSURANCE POLICY

        Policy Number: POL-2026-500

        Policy Holder: Rahul Sharma

        Vehicle Registration: TS09AB1234

        Coverage Type: Comprehensive

        Policy Start Date: 2026-01-01

        Policy End Date: 2026-12-31

        Coverage Limit: 100000

        Deductible: 10000
        """,
    )

    claim_pdf = tmp_path / "claim_form.pdf"

    create_pdf(
        claim_pdf,
        """
        INSURANCE CLAIM FORM

        Claim ID: CLM-500

        Policy Number: POL-2026-500

        Claimant Name: Rahul Sharma

        Claim Type: Motor Vehicle Accident

        Incident Date: 2026-09-05

        Reported Date: 2026-09-06

        Vehicle Registration: TS09AB1234
        """,
    )

    police_pdf = tmp_path / "police_report.pdf"

    create_pdf(
        police_pdf,
        """
        POLICE ACCIDENT REPORT

        Police Report Number: FIR-500

        Claim ID: CLM-500

        Policy Number: POL-2026-500

        Incident Date: 2026-09-05

        Vehicle Registration: TS09AB1234
        """,
    )

    repair_pdf = tmp_path / "repair_estimate.pdf"

    create_pdf(
        repair_pdf,
        """
        VEHICLE REPAIR ESTIMATE

        Claim ID: CLM-500

        Policy Number: POL-2026-500

        Vehicle Registration: TS09AB1234

        Estimated Repair Cost: 85000

        Parts Cost: 60000

        Labor Cost: 25000
        """,
    )

    # ---------------------------------------------------------
    # Step 2: Extract structured data from actual PDFs
    # ---------------------------------------------------------

    extraction_service = StructuredExtractionService()

    policy_structured = (
        extraction_service.process_document(
            file_path=str(policy_pdf),
            claim_id="CLM-500",
            document_id="DOC-POLICY-500",
        )
    )

    claim_structured = (
        extraction_service.process_document(
            file_path=str(claim_pdf),
            claim_id="CLM-500",
            document_id="DOC-CLAIM-500",
        )
    )

    police_structured = (
        extraction_service.process_document(
            file_path=str(police_pdf),
            claim_id="CLM-500",
            document_id="DOC-POLICE-500",
        )
    )

    repair_structured = (
        extraction_service.process_document(
            file_path=str(repair_pdf),
            claim_id="CLM-500",
            document_id="DOC-REPAIR-500",
        )
    )

    # ---------------------------------------------------------
    # Step 3: Verify document classification
    # ---------------------------------------------------------

    assert policy_structured.document_type == "POLICY"

    assert claim_structured.document_type == "CLAIM_FORM"

    assert (
        police_structured.document_type
        == "POLICE_REPORT"
    )

    assert (
        repair_structured.document_type
        == "REPAIR_ESTIMATE"
    )

    # ---------------------------------------------------------
    # Step 4: Verify extracted fields
    # ---------------------------------------------------------

    assert (
        policy_structured.extracted_data[
            "policy_number"
        ]
        == "POL-2026-500"
    )

    assert (
        claim_structured.extracted_data[
            "claim_id"
        ]
        == "CLM-500"
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
        == "TS09AB1234"
    )

    assert (
        repair_structured.extracted_data[
            "estimated_repair_cost"
        ]
        == "85000"
    )

    assert (
        repair_structured.extracted_data[
            "parts_cost"
        ]
        == "60000"
    )

    assert (
        repair_structured.extracted_data[
            "labor_cost"
        ]
        == "25000"
    )

    # ---------------------------------------------------------
    # Step 5: Map structured documents
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

    repair_estimate = mapper.map_document(
        repair_structured
    )

    # ---------------------------------------------------------
    # Step 6: Build claim object
    # ---------------------------------------------------------

    claim = Claim(
        claim_id="CLM-500",
        policy_number="POL-2026-500",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date=claim_form.incident_date,
        reported_date=claim_form.reported_date,
        vehicle_registration=(
            claim_form.vehicle_registration
        ),
    )

    # ---------------------------------------------------------
    # Step 7: Run complete evaluation pipeline
    # ---------------------------------------------------------

    pipeline = ClaimEvaluationPipeline()

    assessment = pipeline.evaluate_claim(
        claim=claim,
        policy=policy,
        claim_form=claim_form,
        police_report=police_report,
        repair_estimate=repair_estimate,
    )

    # ---------------------------------------------------------
    # Step 8: Verify final result
    # ---------------------------------------------------------

    assert assessment.overall_result == "REVIEW"

    # Damage photo is required for motor claims,
    # but was intentionally not supplied.
    assert "DAMAGE_PHOTO" in assessment.missing_documents

    # Policy checks should pass.
    assert all(
        result.result == "PASS"
        for result in assessment.policy_results
    )

    # Existing document consistency checks should pass.
    assert all(
        result.result == "PASS"
        for result in assessment.invariant_results
    )

    # Repair cost should be within coverage.
    assert (
        assessment.expense_results[0].result
        == "PASS"
    )

    # Parts + labor = total repair cost.
    assert (
        assessment.expense_results[1].result
        == "PASS"
    )
    settings.database_path = original_database_path