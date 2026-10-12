from src.db.schema import initialize_database
from src.models.schemas import ExtractedEvidence
from src.services.evidence_service import EvidenceService


def test_save_and_get_claim_evidence():
    initialize_database()

    service = EvidenceService()

    evidence = ExtractedEvidence(
        evidence_id="EVD-001",
        claim_id="TEST-001",
        document_id="DOC-001",
        field_name="incident_date",
        field_value="2026-08-10",
        confidence=0.96,
        page_number=2,
        evidence_text="Date of accident: 10/08/2026",
    )

    service.save_evidence(evidence)

    results = service.get_claim_evidence("TEST-001")

    assert len(results) == 1
    assert results[0].evidence_id == "EVD-001"
    assert results[0].field_name == "incident_date"
    assert results[0].field_value == "2026-08-10"
    assert results[0].confidence == 0.96
    assert results[0].page_number == 2