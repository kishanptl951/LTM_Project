from pathlib import Path
import shutil

from src.config import settings
from src.models.schemas import ClaimDocument
from src.services.document_service import DocumentService


class IngestionService:

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    def __init__(self) -> None:
        self.document_service = DocumentService()

    def ingest_document(
        self,
        claim_id: str,
        document_id: str,
        document_type: str,
        source_path: str,
    ) -> ClaimDocument:
        source = Path(source_path)

        if not source.exists():
            raise FileNotFoundError(
                f"Source document not found: {source_path}"
            )

        if source.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document type: {source.suffix}"
            )

        if source.stat().st_size == 0:
            raise ValueError(
                f"Source document is empty: {source_path}"
            )

        input_directory = Path(settings.input_dir)
        input_directory.mkdir(parents=True, exist_ok=True)

        destination = input_directory / f"{document_id}{source.suffix.lower()}"

        shutil.copy2(source, destination)

        document = ClaimDocument(
            document_id=document_id,
            claim_id=claim_id,
            document_type=document_type,
            file_name=source.name,
            file_path=str(destination),
        )

        self.document_service.register_document(document)

        return document