import logging
from pathlib import Path

from src.models.schemas import DamagePhotoDocument
from .vision_api_client import VisionAPIClient
from .vision_api_schema import VisionAnalysisResponse

logger = logging.getLogger(__name__)


class VisionExtractionService:
    """
    Service responsible for sending damage images to the
    remote Qwen2-VL vision API and converting the response
    into a ClaimGuard DamagePhotoDocument.
    """

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

    def __init__(
        self,
        vision_api_url: str | None = None,
        timeout: int = 120,
    ):
        self.client = VisionAPIClient(
            base_url=vision_api_url or "",
            timeout=timeout,
        )

    def validate_image(self, file_path: str) -> None:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Image not found: {file_path}"
            )

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format: {path.suffix}"
            )

    def create_damage_document(
        self,
        claim_id: str | None,
        vehicle_registration: str | None,
        photo_description: str | None,
        damage_area: str | None,
        visible_damage: str | None,
        estimated_severity: str | None,
    ) -> DamagePhotoDocument:
        """
        Convert structured vision-model output into
        ClaimGuard's DamagePhotoDocument.
        """

        return DamagePhotoDocument(
            claim_id=claim_id,
            vehicle_registration=vehicle_registration,
            photo_description=photo_description,
            damage_area=damage_area,
            visible_damage=visible_damage,
            estimated_severity=estimated_severity,
        )

    def extract_damage(
        self,
        file_path: str,
        claim_id: str | None = None,
    ) -> DamagePhotoDocument:
        """
        Send a damage image to Qwen2-VL through the remote
        vision API and convert the response into a
        DamagePhotoDocument.
        """

        self.validate_image(file_path)

        if not self.client.base_url:
            logger.info("Vision API URL is not set. Returning unanalyzed photo document.")
            return self.create_damage_document(
                claim_id=claim_id,
                vehicle_registration=None,
                photo_description=f"Damage photo provided ({Path(file_path).name}), but VISION_API_URL is not configured.",
                damage_area=None,
                visible_damage=None,
                estimated_severity=None,
            )

        raw_result = self.client.analyze_image(file_path)
        validated = VisionAnalysisResponse.model_validate(raw_result)

        return self.create_damage_document(
            claim_id=claim_id,
            vehicle_registration=validated.vehicle_registration,
            photo_description=validated.photo_description,
            damage_area=validated.damage_area,
            visible_damage=validated.visible_damage,
            estimated_severity=validated.estimated_severity,
        )