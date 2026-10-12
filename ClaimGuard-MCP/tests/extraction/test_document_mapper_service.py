from datetime import date

from src.extraction.document_mapper_service import (
    DocumentMapperService,
)
from src.models.schemas import StructuredDocument


def test_map_claim_form():

    document = StructuredDocument(
        document_id="DOC-001",
        claim_id="CLM-001",
        document_type="CLAIM_FORM",
        extracted_data={
            "claim_id": "CLM-001",
            "policy_number": "POL-2026-001",
            "claimant_name": "Rahul Sharma",
            "claim_type": "Motor Vehicle Accident",
            "incident_date": "2026-09-05",
            "reported_date": "2026-09-06",
            "vehicle_registration": "TS09AB1234",
        },
    )

    mapper = DocumentMapperService()

    result = mapper.map_document(document)

    assert result.claim_id == "CLM-001"
    assert result.policy_number == "POL-2026-001"
    assert result.claimant_name == "Rahul Sharma"
    assert result.incident_date == date(2026, 9, 5)
    assert result.reported_date == date(2026, 9, 6)
    assert result.vehicle_registration == "TS09AB1234"


def test_map_policy():

    document = StructuredDocument(
        document_id="DOC-002",
        claim_id="CLM-001",
        document_type="POLICY",
        extracted_data={
            "policy_number": "POL-2026-001",
            "claimant_name": "Rahul Sharma",
            "vehicle_registration": "TS09AB1234",
            "policy_start_date": "2026-01-01",
            "policy_end_date": "2026-12-31",
        },
    )

    mapper = DocumentMapperService()

    result = mapper.map_document(document)

    assert result.policy_number == "POL-2026-001"
    assert result.policy_holder == "Rahul Sharma"
    assert result.vehicle_registration == "TS09AB1234"
    assert result.policy_start_date == date(2026, 1, 1)
    assert result.policy_end_date == date(2026, 12, 31)


def test_map_police_report():

    document = StructuredDocument(
        document_id="DOC-003",
        claim_id="CLM-001",
        document_type="POLICE_REPORT",
        extracted_data={
            "claim_id": "CLM-001",
            "police_report_number": "HYD-2026-001",
            "vehicle_registration": "TS09XY5678",
            "incident_date": "2026-09-05",
        },
    )

    mapper = DocumentMapperService()

    result = mapper.map_document(document)

    assert result.claim_id == "CLM-001"
    assert result.report_number == "HYD-2026-001"
    assert result.vehicle_registration == "TS09XY5678"
    assert result.incident_date == date(2026, 9, 5)