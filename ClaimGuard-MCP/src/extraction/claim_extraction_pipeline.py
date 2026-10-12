from pathlib import Path

from src.models.schemas import ExtractedEvidence
from src.ingestion.extraction_service import ExtractionService
from src.extraction.field_extraction_service import FieldExtractionService


class ClaimExtractionPipeline:

    def __init__(self) -> None:
        self.extraction_service = ExtractionService()
        self.field_extraction_service = FieldExtractionService()

    def process_document(
        self,
        file_path: str,
        claim_id: str,
        document_id: str,
    ) -> list[ExtractedEvidence]:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        extension = path.suffix.lower()

        if extension == ".pdf":
            return self._process_pdf(
                file_path=file_path,
                claim_id=claim_id,
                document_id=document_id,
            )

        if extension in {".png", ".jpg", ".jpeg"}:
            return self._process_image(
                file_path=file_path,
                claim_id=claim_id,
                document_id=document_id,
            )

        raise ValueError(
            f"Unsupported document type: {extension}"
        )

    def _process_pdf(
        self,
        file_path: str,
        claim_id: str,
        document_id: str,
    ) -> list[ExtractedEvidence]:

        pages = self.extraction_service.extract_pdf_pages(
            file_path
        )

        all_evidence = []

        for page in pages:
            evidence = self.field_extraction_service.extract_and_save_fields(
                text=page.text,
                claim_id=claim_id,
                document_id=document_id,
                page_number=page.page_number,
            )

            all_evidence.extend(evidence)

        return all_evidence

    def _process_image(
        self,
        file_path: str,
        claim_id: str,
        document_id: str,
    ) -> list[ExtractedEvidence]:

        text = self.extraction_service.extract_text_from_image(
            file_path
        )

        return self.field_extraction_service.extract_and_save_fields(
            text=text,
            claim_id=claim_id,
            document_id=document_id,
            page_number=1,
        )