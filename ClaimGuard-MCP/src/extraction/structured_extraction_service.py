import logging
from pathlib import Path

from src.models.schemas import ExtractedEvidence, StructuredDocument
from src.ingestion.document_classifier_service import (
    DocumentClassifierService,
)
from src.ingestion.extraction_service import ExtractionService
from src.extraction.field_extraction_service import (
    FieldExtractionService,
)
from src.extraction.document_mapper_service import (
    DocumentMapperService,
)
from src.extraction.llm_extraction_service import (
    LLMExtractionService,
)
from src.extraction.translation_service import TranslationService
from src.services.evidence_service import EvidenceService

logger = logging.getLogger(__name__)


class StructuredExtractionService:

    def __init__(
        self,
        extraction_service: ExtractionService | None = None,
        classifier_service: DocumentClassifierService | None = None,
        field_extraction_service: FieldExtractionService | None = None,
        evidence_service: EvidenceService | None = None,
        document_mapper_service: DocumentMapperService | None = None,
        llm_extraction_service: LLMExtractionService | None = None,
        translation_service: TranslationService | None = None,
    ) -> None:
        self.extraction_service = extraction_service or ExtractionService()
        self.classifier_service = classifier_service or DocumentClassifierService()
        self.field_extraction_service = (
            field_extraction_service or FieldExtractionService()
        )
        self.evidence_service = evidence_service or EvidenceService()
        self.document_mapper_service = (
            document_mapper_service or DocumentMapperService()
        )
        self.llm_extraction_service = (
            llm_extraction_service or LLMExtractionService()
        )
        self.translation_service = (
            translation_service
            or TranslationService(
                llm_extraction_service=self.llm_extraction_service
            )
        )

    def process_document(
        self,
        file_path: str,
        claim_id: str,
        document_id: str,
    ) -> StructuredDocument:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        extension = path.suffix.lower()

        if extension == ".pdf":
            text = self.extraction_service.extract_text_from_pdf(
                file_path
            )

        elif extension in {".png", ".jpg", ".jpeg"}:
            text = self.extraction_service.extract_text_from_image(
                file_path
            )

        else:
            raise ValueError(
                f"Unsupported document type: {extension}"
            )

        # Pre-normalize Indic numerals in extracted text so date and number regexes match
        normalized_text = self.translation_service.normalize_indic_digits(text)

        document_type = self.classifier_service.classify(
            file_path=file_path,
            text=normalized_text,
        )

        # ---------------------------------------------------------
        # Tier 1: Fast Regex Extraction (Deterministic & Free)
        # ---------------------------------------------------------
        evidence = self.field_extraction_service.extract_fields(
            text=normalized_text,
            claim_id=claim_id,
            document_id=document_id,
        )

        extracted_data = {
            item.field_name: item.field_value
            for item in evidence
            if item.field_value is not None
        }

        # ---------------------------------------------------------
        # Check Critical Fields:
        # policy_number, incident_date, vehicle_registration
        # ---------------------------------------------------------
        critical_fields = [
            "policy_number",
            "incident_date",
            "vehicle_registration",
        ]
        if document_type.value == "POLICY":
            critical_fields = [
                "policy_number",
                "policy_start_date",
                "vehicle_registration",
            ]

        missing_critical = [
            f for f in critical_fields
            if not extracted_data.get(f)
        ]

        # ---------------------------------------------------------
        # Tier 2: LLM Extraction Fallback (OpenAI / Gemini)
        # ---------------------------------------------------------
        if missing_critical and self.llm_extraction_service.is_available():
            logger.info(
                "Document '%s' missing critical fields %s after Tier-1 regex. "
                "Triggering Tier-2 LLM extraction fallback...",
                document_id,
                missing_critical,
            )
            llm_results = self.llm_extraction_service.extract_fields(
                text=normalized_text,
                missing_fields=missing_critical,
            )

            # Merge LLM results for any missing fields
            for field_name, field_value in llm_results.items():
                if field_value is not None and str(field_value).strip():
                    if not extracted_data.get(field_name):
                        clean_value = str(field_value).strip()
                        extracted_data[field_name] = clean_value
                        llm_evidence = ExtractedEvidence(
                            evidence_id=f"{document_id}-{field_name}",
                            claim_id=claim_id,
                            document_id=document_id,
                            field_name=field_name,
                            field_value=clean_value,
                            confidence=0.85,
                            evidence_text=f"[Tier-2 LLM Fallback: {field_name}]",
                        )
                        evidence.append(llm_evidence)

        # ---------------------------------------------------------
        # Tier 3: Multi-Language Translation & Transliteration Pipeline
        # ---------------------------------------------------------
        extracted_data = self.translation_service.translate_fields(extracted_data)

        # Synchronize evidence list with translated/transliterated values
        for item in evidence:
            if item.field_name in extracted_data:
                item.field_value = str(extracted_data[item.field_name])

        # Persist extracted evidence so downstream evaluation
        # can retrieve the evidence associated with this claim.
        for item in evidence:
            self.evidence_service.save_evidence(item)

        return StructuredDocument(
            document_id=document_id,
            claim_id=claim_id,
            document_type=document_type.value,
            extracted_data=extracted_data,
            confidence=1.0 if evidence else None,
        )

    def process_and_map_document(
        self,
        file_path: str,
        claim_id: str,
        document_id: str,
    ):
        structured_document = self.process_document(
            file_path=file_path,
            claim_id=claim_id,
            document_id=document_id,
        )

        return self.document_mapper_service.map_document(
            structured_document
        )