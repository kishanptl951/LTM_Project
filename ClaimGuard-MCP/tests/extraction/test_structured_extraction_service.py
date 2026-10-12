from pathlib import Path

from src.extraction.structured_extraction_service import (
    StructuredExtractionService,
)


def test_process_document():
    file_path = Path("data/sample_claims/sample_claim.pdf")

    service = StructuredExtractionService()

    result = service.process_document(
        file_path=str(file_path),
        claim_id="TEST-STRUCTURED-001",
        document_id="DOC-STRUCTURED-001",
    )

    assert result.document_id == "DOC-STRUCTURED-001"
    assert result.claim_id == "TEST-STRUCTURED-001"
    assert result.document_type == "CLAIM_FORM"

    assert result.extracted_data["claim_id"] == "CLM-001"
    assert result.extracted_data["policy_number"] == "POL-2026-001"
    assert result.extracted_data["claimant_name"] == "Rahul Sharma"
    assert result.extracted_data["vehicle_registration"] == "TS09AB1234"


def test_process_document_with_regional_language_and_indic_digits(tmp_path):
    class MockExtractionService:

        def extract_text_from_pdf(self, file_path):
            return """
            Insurance Claim Form
            Claim ID: CLM-HIN-01
            Policy Number: POL-2026-789
            Incident Date: २०२६-०९-०५
            Claimant Name: राहुल शर्मा
            Vehicle Registration: TS09AB1234
            """

        def extract_text_from_image(self, file_path):
            return self.extract_text_from_pdf(file_path)

    dummy_file = tmp_path / "claim_hindi.pdf"
    dummy_file.write_text("dummy")

    service = StructuredExtractionService(
        extraction_service=MockExtractionService()
    )

    result = service.process_document(
        file_path=str(dummy_file),
        claim_id="CLM-HIN-01",
        document_id="DOC-HIN-01",
    )

    assert result.document_type == "CLAIM_FORM"
    assert result.extracted_data["claim_id"] == "CLM-HIN-01"
    assert result.extracted_data["policy_number"] == "POL-2026-789"
    # Indic numerals normalized
    assert result.extracted_data["incident_date"] == "2026-09-05"
    # Hindi name transliterated to Latin
    assert "Rahul" in result.extracted_data["claimant_name"]
    assert "Sharma" in result.extracted_data["claimant_name"]