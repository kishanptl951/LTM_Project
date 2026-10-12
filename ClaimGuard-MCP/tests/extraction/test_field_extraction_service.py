from src.extraction.field_extraction_service import FieldExtractionService


def test_extract_claim_fields():
    service = FieldExtractionService()

    text = """
    Claim ID: CLM-001
    Policy Number: POL-2026-001
    Claimant Name: Rahul Sharma
    Claim Type: Motor Vehicle Accident
    Incident Date: 2026-09-05
    Reported Date: 2026-09-06
    Vehicle Registration: TS09AB1234
    Vehicle Make: Toyota
    Vehicle Model: Corolla
    Police Report Number: HYD-2026-0915
    Estimated Repair Cost: INR 85,000
    """

    results = service.extract_fields(
        text=text,
        claim_id="CLM-001",
        document_id="DOC-001",
        page_number=1,
    )

    assert len(results) == 11

    fields = {
        result.field_name: result
        for result in results
    }

    assert fields["claim_id"].field_value == "CLM-001"
    assert fields["policy_number"].field_value == "POL-2026-001"
    assert fields["claimant_name"].field_value == "Rahul Sharma"
    assert fields["incident_date"].field_value == "2026-09-05"
    assert fields["reported_date"].field_value == "2026-09-06"
    assert fields["vehicle_registration"].field_value == "TS09AB1234"
    assert fields["vehicle_make"].field_value == "Toyota"
    assert fields["vehicle_model"].field_value == "Corolla"
    assert fields["police_report_number"].field_value == "HYD-2026-0915"
    assert fields["estimated_repair_cost"].field_value == "INR 85,000"


def test_extract_fields_preserves_evidence():
    service = FieldExtractionService()

    text = "Incident Date: 2026-09-05"

    results = service.extract_fields(
        text=text,
        claim_id="CLM-001",
        document_id="DOC-001",
        page_number=2,
    )

    assert len(results) == 1

    result = results[0]

    assert result.field_name == "incident_date"
    assert result.field_value == "2026-09-05"
    assert result.page_number == 2
    assert result.evidence_text == "Incident Date: 2026-09-05"
    assert result.confidence == 1.0
from src.db.schema import initialize_database
from src.db.session import get_db_connection


def test_extract_and_save_fields():
    initialize_database()

    service = FieldExtractionService()

    text = """
    Incident Date: 2026-09-05
    Vehicle Registration: TS09AB1234
    """

    results = service.extract_and_save_fields(
        text=text,
        claim_id="TEST-FIELD-001",
        document_id="DOC-FIELD-001",
        page_number=1,
    )

    assert len(results) == 2

    with get_db_connection() as conn:

        rows = conn.execute(
            """
            SELECT field_name, field_value
            FROM extracted_evidence
            WHERE claim_id = ?
            ORDER BY field_name
            """,
            ["TEST-FIELD-001"],
        ).fetchall()

    assert rows == [
        ("incident_date", "2026-09-05"),
        ("vehicle_registration", "TS09AB1234"),
    ]