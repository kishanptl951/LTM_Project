from pathlib import Path
from src.db.session import get_db_connection

import fitz

from src.extraction.claim_extraction_pipeline import ClaimExtractionPipeline
from src.evaluation.invariant_evaluation_service import (
    InvariantEvaluationService,
)
from src.models.schemas import ClaimFormDocument, PolicyDocument


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
    with get_db_connection() as conn:

        conn.execute(
            """
            DELETE FROM invariant_results
            WHERE claim_id = 'CLM-200'
            """
        )

        conn.execute(
            """
            DELETE FROM policy_evaluations
            WHERE claim_id = 'CLM-200'
            """
        )

        conn.execute(
            """
            DELETE FROM extracted_evidence
            WHERE claim_id = 'CLM-200'
            """
        )

        conn.execute(
            """
            DELETE FROM documents
            WHERE claim_id = 'CLM-200'
            """
        )

        conn.execute(
            """
            DELETE FROM claims
            WHERE claim_id = 'CLM-200'
            """
        )


def test_vehicle_registration_mismatch(tmp_path):
    clean_test_data()
    claim_id = "CLM-200"

    claim_form_path = tmp_path / "claim_form.pdf"
    policy_path = tmp_path / "policy.pdf"

    create_pdf(
        claim_form_path,
        """
MOTOR VEHICLE INSURANCE CLAIM FORM

Claim ID: CLM-200
Policy Number: POL-2026-200
Claimant Name: Rahul Sharma

Vehicle Registration: TS09AB1234
Vehicle Make: Toyota
Vehicle Model: Corolla

Incident Date: 2026-09-05
""",
    )

    create_pdf(
        policy_path,
        """
MOTOR INSURANCE POLICY

Policy Number: POL-2026-200
Claimant Name: Rahul Sharma

Vehicle Registration: TS09XY5678
Vehicle Make: Toyota
Vehicle Model: Corolla

Policy Start Date: 2026-01-01
Policy End Date: 2026-12-31
""",
    )

    pipeline = ClaimExtractionPipeline()

    claim_form_evidence = pipeline.process_document(
        file_path=str(claim_form_path),
        claim_id=claim_id,
        document_id="TEST-CLAIM-FORM-200",
    )

    policy_evidence = pipeline.process_document(
        file_path=str(policy_path),
        claim_id=claim_id,
        document_id="TEST-POLICY-200",
    )

    claim_form_fields = {
        result.field_name: result.field_value
        for result in claim_form_evidence
    }

    policy_fields = {
        result.field_name: result.field_value
        for result in policy_evidence
    }

    # Confirm extraction found the conflicting facts.
    assert claim_form_fields["vehicle_registration"] == "TS09AB1234"
    assert policy_fields["vehicle_registration"] == "TS09XY5678"

    claim_form = ClaimFormDocument(
        document_id="TEST-CLAIM-FORM-200",
        claim_id=claim_id,
        document_type="CLAIM_FORM",
        policy_number=claim_form_fields["policy_number"],
        vehicle_registration=claim_form_fields["vehicle_registration"],
        fields=claim_form_fields,
    )

    policy = PolicyDocument(
        document_id="TEST-POLICY-200",
        claim_id=claim_id,
        document_type="POLICY",
        policy_number=policy_fields["policy_number"],
        vehicle_registration=policy_fields["vehicle_registration"],
        fields=policy_fields,
    )

    invariant_service = InvariantEvaluationService()

    result = invariant_service.check_vehicle_registration(
        claim_form=claim_form,
        policy=policy,
    )

    # The invariant engine must detect the mismatch.
    assert result.result == "FAIL"
    assert result.severity == "HIGH"

    assert "TS09AB1234" in result.explanation
    assert "TS09XY5678" in result.explanation