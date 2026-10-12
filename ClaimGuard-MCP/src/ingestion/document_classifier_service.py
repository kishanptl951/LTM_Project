import logging
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.ingestion.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    POLICY = "POLICY"
    CLAIM_FORM = "CLAIM_FORM"
    POLICE_REPORT = "POLICE_REPORT"
    MEDICAL_BILL = "MEDICAL_BILL"
    REPAIR_ESTIMATE = "REPAIR_ESTIMATE"
    DAMAGE_PHOTO = "DAMAGE_PHOTO"
    OTHER = "OTHER"


class DocumentClassifierService:

    def __init__(
        self,
        extraction_service: "ExtractionService | None" = None,
    ) -> None:
        self._extraction_service = extraction_service

    @property
    def extraction_service(self):
        if self._extraction_service is None:
            from src.ingestion.extraction_service import ExtractionService

            self._extraction_service = ExtractionService()
        return self._extraction_service

    def classify(
        self,
        file_path: str,
        text: str | None = None,
    ) -> DocumentType:

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {file_path}"
            )

        extension = path.suffix.lower()

        # If text is not provided, run OCR for images or extract text for PDFs
        if not text or not text.strip():
            if extension in {".png", ".jpg", ".jpeg"}:
                try:
                    ocr_text = self.extraction_service.extract_text_from_image(
                        file_path
                    )
                    if ocr_text and ocr_text.strip():
                        text = ocr_text.strip()
                except Exception as exc:
                    logger.debug(
                        "OCR extraction failed for image %s: %s",
                        file_path,
                        exc,
                    )
            elif extension == ".pdf":
                try:
                    pdf_text = self.extraction_service.extract_text_from_pdf(
                        file_path
                    )
                    if pdf_text and pdf_text.strip():
                        text = pdf_text.strip()
                except Exception as exc:
                    logger.debug(
                        "Text extraction failed for PDF %s: %s",
                        file_path,
                        exc,
                    )

        if not text or not text.strip():
            if extension in {".png", ".jpg", ".jpeg"}:
                return DocumentType.DAMAGE_PHOTO
            return DocumentType.OTHER

        normalized_text = text.lower()

        # ---------------------------------------------------------
        # POLICY
        # ---------------------------------------------------------
        policy_indicators = [
            "policy start date",
            "policy end date",
            "policy period",
            "coverage",
            "premium",
            "deductible",
            "coverage limit",
            "sum insured",
            "insured name",
        ]
        if (
            "policy number" in normalized_text
            or "policy no" in normalized_text
            or "policy #" in normalized_text
        ):
            if any(
                indicator in normalized_text
                for indicator in policy_indicators
            ):
                return DocumentType.POLICY
        if (
            "insurance policy" in normalized_text
            or "policy schedule" in normalized_text
            or "policy document" in normalized_text
            or "बीमा पॉलिसी" in normalized_text
            or "पॉलिसी संख्या" in normalized_text
            or "पालिसी संख्या" in normalized_text
            or "భీమా పాలసీ" in normalized_text
            or "పాలసీ నంబర్" in normalized_text
            or "காப்பீட்டுக் கொள்கை" in normalized_text
            or "பாலிசி எண்" in normalized_text
        ):
            return DocumentType.POLICY
        if "policy" in normalized_text and any(
            k in normalized_text
            for k in [
                "premium",
                "coverage",
                "deductible",
                "sum insured",
                "policy period",
            ]
        ):
            return DocumentType.POLICY

        # ---------------------------------------------------------
        # CLAIM FORM
        # ---------------------------------------------------------
        if (
            "claim form" in normalized_text
            or "motor claim form" in normalized_text
            or "दावा प्रपत्र" in normalized_text
            or "दावा फॉर्म" in normalized_text
            or "बीमा दावा" in normalized_text
            or "క్లెయిమ్ ఫారమ్" in normalized_text
            or "கோரிக்கை படிவம்" in normalized_text
            or (
                (
                    "claim id" in normalized_text
                    or "claim number" in normalized_text
                    or "claim no" in normalized_text
                )
                and (
                    "incident date" in normalized_text
                    or "date of incident" in normalized_text
                    or "date of accident" in normalized_text
                )
                and (
                    "claimant name" in normalized_text
                    or "claimant" in normalized_text
                )
            )
        ):
            return DocumentType.CLAIM_FORM

        # ---------------------------------------------------------
        # POLICE REPORT
        # ---------------------------------------------------------
        if (
            "police report" in normalized_text
            or "police accident report" in normalized_text
            or "police station" in normalized_text
            or "fir number" in normalized_text
            or "fir no" in normalized_text
            or "first information report" in normalized_text
            or "पुलिस स्टेशन" in normalized_text
            or "थाना" in normalized_text
            or "प्राथमिकी" in normalized_text
            or "प्रथम सूचना रिपोर्ट" in normalized_text
            or "पोलीस ठाणे" in normalized_text
            or "पोलीस स्टेशन" in normalized_text
            or "పోలీస్ స్టేషన్" in normalized_text
            or "காவல் நிலையம்" in normalized_text
            or (
                "report number" in normalized_text
                and (
                    "police" in normalized_text
                    or "station" in normalized_text
                )
            )
            or (
                "fir" in normalized_text.split()
                and any(
                    w in normalized_text
                    for w in [
                        "police",
                        "station",
                        "incident",
                        "accident",
                        "officer",
                        "inspector",
                    ]
                )
            )
        ):
            return DocumentType.POLICE_REPORT

        # ---------------------------------------------------------
        # MEDICAL BILL
        # ---------------------------------------------------------
        if (
            "hospital" in normalized_text
            or "patient" in normalized_text
            or "medical bill" in normalized_text
            or "hospital bill" in normalized_text
            or "discharge summary" in normalized_text
            or "inpatient" in normalized_text
            or "अस्पताल" in normalized_text
            or "चिकित्सा बिल" in normalized_text
            or "मरीज" in normalized_text
            or "रोगी" in normalized_text
            or "ఆసుపత్రి" in normalized_text
            or "மருத்துவமனை" in normalized_text
        ):
            return DocumentType.MEDICAL_BILL

        # ---------------------------------------------------------
        # REPAIR ESTIMATE
        # ---------------------------------------------------------
        if (
            "repair estimate" in normalized_text
            or "repair cost" in normalized_text
            or "labor charges" in normalized_text
            or "repair invoice" in normalized_text
            or "estimate of repair" in normalized_text
            or "garage estimate" in normalized_text
            or "workshop estimate" in normalized_text
            or "मरम्मत अनुमान" in normalized_text
            or "मरम्मत लागत" in normalized_text
            or "श्रम शुल्क" in normalized_text
            or "మరమ్మతు అంచనా" in normalized_text
            or "பழுதுபார்ப்பு மதிப்பீடு" in normalized_text
            or (
                "repair" in normalized_text
                and any(
                    w in normalized_text
                    for w in [
                        "estimate",
                        "quotation",
                        "labor",
                        "labour",
                        "parts",
                        "cost",
                    ]
                )
            )
        ):
            return DocumentType.REPAIR_ESTIMATE

        if extension in {".png", ".jpg", ".jpeg"}:
            return DocumentType.DAMAGE_PHOTO

        return DocumentType.OTHER