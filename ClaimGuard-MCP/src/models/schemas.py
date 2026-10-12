from datetime import date, datetime

from pydantic import BaseModel, Field


class ClaimDocument(BaseModel):
    document_id: str
    claim_id: str
    document_type: str
    file_name: str
    file_path: str
    created_at: datetime | None = None


class Claim(BaseModel):
    claim_id: str
    policy_number: str | None = None
    claimant_name: str | None = None
    claim_type: str | None = None
    incident_date: date | None = None
    reported_date: date | None = None
    vehicle_registration: str | None = None
    status: str = "PENDING"
    created_at: datetime | None = None


class ExtractedEvidence(BaseModel):
    evidence_id: str
    claim_id: str
    document_id: str
    field_name: str
    field_value: str | None = None
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )
    page_number: int | None = None
    evidence_text: str | None = None
    created_at: datetime | None = None


class PolicyEvaluation(BaseModel):
    evaluation_id: str
    claim_id: str
    rule_id: str
    result: str
    explanation: str | None = None

    repair_cost: float | None = None
    coverage_limit: float | None = None
    deductible: float | None = None
    estimated_payable: float | None = None

    created_at: datetime | None = None


class InvariantResult(BaseModel):
    result_id: str
    claim_id: str
    invariant_id: str
    result: str
    severity: str | None = None
    explanation: str | None = None
    created_at: datetime | None = None


class ExtractionResult(BaseModel):
    document_id: str
    page_number: int | None = None
    text: str
    source_type: str


class PolicyDocument(BaseModel):
    policy_number: str
    policy_holder: str | None = None
    vehicle_registration: str | None = None
    coverage_type: str | None = None
    policy_start_date: date | None = None
    policy_end_date: date | None = None
    deductible: float | None = None
    coverage_limit: float | None = None


class ClaimFormDocument(BaseModel):
    claim_id: str
    policy_number: str | None = None
    claimant_name: str | None = None
    claim_type: str | None = None
    incident_date: date | None = None
    reported_date: date | None = None
    incident_location: str | None = None
    incident_description: str | None = None
    vehicle_registration: str | None = None


class PoliceReportDocument(BaseModel):
    report_number: str | None = None
    claim_id: str | None = None
    policy_number: str | None = None
    incident_date: date | None = None
    incident_time: str | None = None
    incident_location: str | None = None
    police_station: str | None = None
    officer_name: str | None = None
    incident_description: str | None = None
    vehicle_registration: str | None = None


class RepairEstimateDocument(BaseModel):
    estimate_number: str | None = None
    claim_id: str | None = None
    policy_number: str | None = None
    vehicle_registration: str | None = None
    repair_date: date | None = None
    workshop_name: str | None = None
    total_estimated_cost: float | None = None
    parts_cost: float | None = None
    labor_cost: float | None = None
    repair_description: str | None = None


class MedicalBillDocument(BaseModel):
    bill_number: str | None = None
    claim_id: str | None = None
    policy_number: str | None = None
    patient_name: str | None = None
    hospital_name: str | None = None
    admission_date: date | None = None
    discharge_date: date | None = None
    diagnosis: str | None = None
    treatment_description: str | None = None
    total_bill_amount: float | None = None


class DamagePhotoDocument(BaseModel):
    claim_id: str | None = None
    vehicle_registration: str | None = None
    photo_description: str | None = None
    damage_area: str | None = None
    visible_damage: str | None = None
    estimated_severity: str | None = None


class StructuredDocument(BaseModel):
    document_id: str
    claim_id: str
    document_type: str
    extracted_data: dict
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


class ClaimAssessment(BaseModel):
    claim_id: str
    overall_result: str
    policy_results: list[PolicyEvaluation] = Field(default_factory=list)
    invariant_results: list[InvariantResult] = Field(default_factory=list)
    expense_results: list[PolicyEvaluation] = Field(default_factory=list)
    damage_results: list[InvariantResult] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    required_documents: list[str] = Field(default_factory=list)
    missing_documents: list[str] = Field(default_factory=list)
    available_documents: list[str] = Field(default_factory=list)