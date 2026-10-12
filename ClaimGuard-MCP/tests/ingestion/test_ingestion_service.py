from pathlib import Path

from src.db.schema import initialize_database
from src.ingestion.ingestion_service import IngestionService


def test_ingest_document(tmp_path):
    initialize_database()

    source_file = Path(tmp_path) / "police_report.pdf"
    source_file.write_bytes(b"fake pdf content")

    service = IngestionService()

    document = service.ingest_document(
        claim_id="TEST-INGEST-001",
        document_id="DOC-INGEST-001",
        document_type="POLICE_REPORT",
        source_path=str(source_file),
    )

    assert document.document_id == "DOC-INGEST-001"
    assert document.claim_id == "TEST-INGEST-001"
    assert document.document_type == "POLICE_REPORT"

    stored_file = Path(document.file_path)

    assert stored_file.exists()
    assert stored_file.name == "DOC-INGEST-001.pdf"

    assert service.document_service.get_document(
        "DOC-INGEST-001"
    ) is not None

def test_ingest_empty_document_rejected(tmp_path):
    initialize_database()

    source_file = Path(tmp_path) / "empty.pdf"
    source_file.write_bytes(b"")

    service = IngestionService()

    try:
        service.ingest_document(
            claim_id="TEST-EMPTY-001",
            document_id="DOC-EMPTY-001",
            document_type="CLAIM_FORM",
            source_path=str(source_file),
        )
        assert False, "Expected empty document to be rejected"
    except ValueError as exc:
        assert "Source document is empty" in str(exc)

    stored_file = Path("data/input/DOC-EMPTY-001.pdf")
    assert not stored_file.exists()