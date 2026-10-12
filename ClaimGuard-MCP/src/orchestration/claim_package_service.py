import logging
from pathlib import Path

from src.config import settings
from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.extraction.document_mapper_service import (
    DocumentMapperService,
)
from src.extraction.structured_extraction_service import (
    StructuredExtractionService,
)
from src.ingestion.document_classifier_service import (
    DocumentClassifierService,
    DocumentType,
)
from src.models.schemas import Claim, ClaimAssessment, ClaimDocument
from src.services.claim_service import ClaimService
from src.services.document_service import DocumentService
from src.services.invariant_service import InvariantService
from src.services.policy_service import PolicyService
from src.vision.vision_extraction_service import (
    VisionExtractionService,
)

logger = logging.getLogger(__name__)


class ClaimPackageService:
    """
    Coordinates processing of a complete insurance claim package.

    Business rules remain in the existing evaluation services.
    This service only orchestrates the workflow.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
    }

    def __init__(
        self,
        vision_extraction_service: VisionExtractionService | None = None,
        classifier_service: DocumentClassifierService | None = None,
    ) -> None:
        self.classifier_service = (
            classifier_service or DocumentClassifierService()
        )
        self.structured_extraction_service = (
            StructuredExtractionService(
                classifier_service=self.classifier_service
            )
        )

        self.document_mapper_service = (
            DocumentMapperService()
        )

        self.vision_extraction_service = (
            vision_extraction_service
            if vision_extraction_service is not None
            else VisionExtractionService(
                vision_api_url=settings.vision_api_url
            )
        )

        self.claim_evaluation_pipeline = (
            ClaimEvaluationPipeline()
        )

        self.claim_service = ClaimService()
        self.document_service = DocumentService()
        self.policy_service = PolicyService()
        self.invariant_service = InvariantService()

    def process_package(
        self,
        package_path: str,
        claim_id: str,
    ) -> ClaimAssessment:
        package = Path(package_path)

        if not package.exists():
            raise FileNotFoundError(
                f"Claim package not found: {package_path}"
            )

        if not package.is_dir():
            raise ValueError(
                f"Claim package path is not a directory: {package_path}"
            )

        files = [
            file
            for file in package.iterdir()
            if file.is_file()
            and file.suffix.lower() in self.SUPPORTED_EXTENSIONS
        ]

        logger.info("Processing claim package: %s", package)
        logger.info("Claim ID: %s", claim_id)

        mapped_documents = {}
        damage_photos: list[DamagePhotoDocument] = []

        # --------------------------------------------------
        # 1. Process documents (PDFs, Scanned Images, Damage Photos)
        # --------------------------------------------------

        for file in files:
            ext = file.suffix.lower()

            # Classify images: are they scanned text documents or actual damage photos?
            if ext in {".png", ".jpg", ".jpeg"}:
                doc_type = self.classifier_service.classify(file_path=str(file))
                if doc_type == DocumentType.DAMAGE_PHOTO:
                    is_damage_photo = True
                else:
                    is_damage_photo = False
                    logger.info(
                        "Smart classification identified image %s as text document: %s",
                        file.name,
                        doc_type.value,
                    )
            elif ext == ".pdf":
                is_damage_photo = False
            else:
                continue

            if is_damage_photo:
                logger.info(
                    "Processing damage photo: %s", file.name
                )

                photo_doc_id = f"{claim_id}-{file.stem}"
                try:
                    self.document_service.register_document(
                        ClaimDocument(
                            document_id=photo_doc_id,
                            claim_id=claim_id,
                            document_type="DAMAGE_PHOTO",
                            file_name=file.name,
                            file_path=str(file),
                        )
                    )
                except Exception as exc:
                    logger.warning("Failed to register photo document %s: %s", photo_doc_id, exc)

                try:
                    damage_document = (
                        self.vision_extraction_service.extract_damage(
                            file_path=str(file),
                            claim_id=claim_id,
                        )
                    )
                except Exception as exc:
                    logger.warning(
                        "Vision analysis failed for photo %s: %s. Continuing with unverified damage photo.",
                        file.name,
                        exc,
                    )
                    damage_document = self.vision_extraction_service.create_damage_document(
                        claim_id=claim_id,
                        vehicle_registration=None,
                        photo_description=(
                            f"Photo provided ({file.name}), but vision analysis "
                            f"was unavailable: {exc}"
                        ),
                        damage_area=None,
                        visible_damage=None,
                        estimated_severity=None,
                    )

                damage_photos.append(damage_document)

                logger.info("  Type: DAMAGE_PHOTO")

                logger.info(
                    "  Damage area: %s",
                    damage_document.damage_area,
                )

                logger.info(
                    "  Severity: %s",
                    damage_document.estimated_severity,
                )

            else:
                logger.info("Processing text document: %s", file.name)

                doc_id = f"{claim_id}-{file.stem}"
                structured_document = (
                    self.structured_extraction_service.process_document(
                        file_path=str(file),
                        claim_id=claim_id,
                        document_id=doc_id,
                    )
                )

                # Persist document metadata
                try:
                    self.document_service.register_document(
                        ClaimDocument(
                            document_id=doc_id,
                            claim_id=claim_id,
                            document_type=structured_document.document_type,
                            file_name=file.name,
                            file_path=str(file),
                        )
                    )
                except Exception as exc:
                    logger.warning("Failed to register document %s: %s", doc_id, exc)

                mapped_document = (
                    self.document_mapper_service.map_document(
                        structured_document
                    )
                )

                mapped_documents[
                    structured_document.document_type
                ] = mapped_document

                logger.info(
                    "  Type: %s", structured_document.document_type
                )

                logger.info(
                    "  Mapped to: %s",
                    type(mapped_document).__name__,
                )

                logger.info(
                    "  Fields extracted: %d",
                    len(structured_document.extracted_data),
                )

        if damage_photos:
            mapped_documents["DAMAGE_PHOTO"] = damage_photos[0]
            mapped_documents["DAMAGE_PHOTOS"] = damage_photos

        # --------------------------------------------------
        # 3. Build the central Claim object
        # --------------------------------------------------

        claim_form = mapped_documents.get(
            "CLAIM_FORM"
        )

        if claim_form is None:
            raise ValueError(
                "Claim package does not contain a claim form."
            )

        policy_doc = mapped_documents.get("POLICY")
        resolved_policy_number = (
            claim_form.policy_number
            or (policy_doc.policy_number if policy_doc and policy_doc.policy_number else None)
            or ""
        )

        claim = Claim(
            claim_id=claim_id,
            policy_number=resolved_policy_number,
            claimant_name=claim_form.claimant_name,
            claim_type=claim_form.claim_type,
            incident_date=claim_form.incident_date,
            reported_date=claim_form.reported_date,
            vehicle_registration=(
                claim_form.vehicle_registration
            ),
            status="PENDING",
        )

        # Persist claim in DuckDB
        try:
            self.claim_service.create_claim(claim)
        except Exception as exc:
            logger.warning("Failed to save claim %s: %s", claim_id, exc)

        logger.info(
            "Claim assembled: %s", claim.claim_id
        )

        # --------------------------------------------------
        # 4. Retrieve required documents
        # --------------------------------------------------

        policy = mapped_documents.get("POLICY")

        if policy is None:
            raise ValueError(
                "Claim package does not contain a policy."
            )

        police_report = mapped_documents.get(
            "POLICE_REPORT"
        )

        repair_estimate = mapped_documents.get(
            "REPAIR_ESTIMATE"
        )

        damage_photo = mapped_documents.get(
            "DAMAGE_PHOTO"
        )

        damage_photos_list = mapped_documents.get(
            "DAMAGE_PHOTOS", []
        )

        medical_bill = mapped_documents.get(
            "MEDICAL_BILL"
        )

        # --------------------------------------------------
        # 5. Run the complete evaluation pipeline
        # --------------------------------------------------

        assessment = (
            self.claim_evaluation_pipeline.evaluate_claim(
                claim=claim,
                policy=policy,
                claim_form=claim_form,
                police_report=police_report,
                repair_estimate=repair_estimate,
                damage_photo=damage_photo,
                damage_photos=damage_photos_list,
                medical_bill=medical_bill,
            )
        )

        # Persist evaluations and update status in DuckDB
        try:
            for pol_res in assessment.policy_results:
                self.policy_service.save_evaluation(pol_res)

            for exp_res in assessment.expense_results:
                self.policy_service.save_evaluation(exp_res)

            for inv_res in assessment.invariant_results:
                self.invariant_service.save_result(inv_res)

            for dam_res in assessment.damage_results:
                self.invariant_service.save_result(dam_res)

            self.claim_service.update_claim_status(
                claim_id=claim_id,
                status=assessment.overall_result,
            )
        except Exception as exc:
            logger.warning("Failed to persist assessment results for claim %s: %s", claim_id, exc)

        logger.info(
            "Final result: %s",
            assessment.overall_result,
        )

        return assessment