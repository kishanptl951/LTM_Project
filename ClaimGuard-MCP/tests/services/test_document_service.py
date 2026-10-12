from pathlib import Path

from src.db.schema import initialize_database
from src.models.schemas import ClaimDocument
from src.services.document_service import DocumentService


def test_register_document(tmp_path):
    initialize_database()

    test_file = Path(tmp_path) / "test_document.pdf"
    test_file.write_bytes(b"test pdf content")

    document = ClaimDocument(
        document_id="DOC-001",
        claim_id="TEST-001",
        document_type="POLICE_REPORT",
        file_name="test_document.pdf",
        file_path=str(test_file),
    )

    service = DocumentService()
    service.register_document(document)

    result = service.get_document("DOC-001")

    assert result is not None
    assert result.document_id == "DOC-001"
    assert result.claim_id == "TEST-001"
    assert result.document_type == "POLICE_REPORT"
    assert result.file_name == "test_document.pdf"