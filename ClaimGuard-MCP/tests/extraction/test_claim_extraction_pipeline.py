from src.db.schema import initialize_database
from src.db.session import get_db_connection
from src.extraction.claim_extraction_pipeline import ClaimExtractionPipeline


def test_process_document():

    initialize_database()

    pipeline = ClaimExtractionPipeline()

    results = pipeline.process_document(
        file_path="data/sample_claims/sample_claim.pdf",
        claim_id="TEST-PIPELINE-001",
        document_id="DOC-PIPELINE-001",
    )

    assert len(results) == 12

    fields = {
        result.field_name: result.field_value
        for result in results
    }

    assert fields["claim_id"] == "CLM-001"
    assert fields["policy_number"] == "POL-2026-001"
    assert fields["claimant_name"] == "Rahul Sharma"
    assert fields["incident_date"] == "2026-09-05"
    assert fields["reported_date"] == "2026-09-06"
    assert fields["vehicle_registration"] == "TS09AB1234"
    assert fields["vehicle_make"] == "Toyota"
    assert fields["vehicle_model"] == "Corolla"
    assert fields["police_report_number"] == "HYD-2026-0915"
    assert fields["estimated_repair_cost"] == "INR 85,000"

    with get_db_connection() as conn:

        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM extracted_evidence
            WHERE claim_id = ?
            """,
            ["TEST-PIPELINE-001"],
        ).fetchone()[0]

    assert count == 12