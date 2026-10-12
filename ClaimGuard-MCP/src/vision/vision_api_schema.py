from pydantic import BaseModel, Field


class VisionAnalysisRequest(BaseModel):
    image: str = Field(
        ...,
        description="Base64-encoded image"
    )


class VisionAnalysisResponse(BaseModel):
    damage_area: str | None = None
    visible_damage: str | None = None
    estimated_severity: str | None = None
    photo_description: str | None = None
    vehicle_registration: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )