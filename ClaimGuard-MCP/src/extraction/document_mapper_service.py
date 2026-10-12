import re
from datetime import date, datetime

from src.models.schemas import (
    ClaimFormDocument,
    DamagePhotoDocument,
    MedicalBillDocument,
    PoliceReportDocument,
    PolicyDocument,
    RepairEstimateDocument,
    StructuredDocument,
)


class DocumentMapperService:

    @staticmethod
    def _parse_date(value: str | None) -> date | None:
        if not value:
            return None

        val = value.strip()
        try:
            return date.fromisoformat(val)
        except ValueError:
            pass

        # Support common formats across regions:
        # DD/MM/YYYY, DD-MM-YYYY, MM/DD/YYYY, and verbal months
        date_formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%m/%d/%Y",
            "%m-%d-%Y",
            "%Y/%m/%d",
            "%d %b %Y",
            "%d %B %Y",
            "%b %d, %Y",
            "%B %d, %Y",
            "%d-%b-%Y",
            "%d-%B-%Y",
        ]
        for fmt in date_formats:
            try:
                return datetime.strptime(val, fmt).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        if not value:
            return None

        cleaned = (
            value.replace(",", "")
            .replace("INR", "")
            .replace("₹", "")
            .replace("USD", "")
            .replace("$", "")
            .replace("EUR", "")
            .replace("€", "")
            .replace("GBP", "")
            .replace("£", "")
            .replace("Rs.", "")
            .replace("Rs", "")
            .replace("/-", "")
            .strip()
        )

        match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
        if match:
            try:
                return float(match.group(0))
            except ValueError:
                return None

        return None

    def map_document(
        self,
        document: StructuredDocument,
    ):
        data = document.extracted_data
        document_type = document.document_type

        if document_type == "CLAIM_FORM":
            return ClaimFormDocument(
                claim_id=data.get("claim_id") or document.claim_id,
                policy_number=data.get("policy_number"),
                claimant_name=data.get("claimant_name"),
                claim_type=data.get("claim_type"),
                incident_date=self._parse_date(
                    data.get("incident_date")
                ),
                reported_date=self._parse_date(
                    data.get("reported_date")
                ),
                incident_location=data.get("incident_location"),
                incident_description=data.get(
                    "incident_description"
                ),
                vehicle_registration=data.get(
                    "vehicle_registration"
                ),
            )

        if document_type == "POLICY":
            return PolicyDocument(
                policy_number=data.get("policy_number", ""),
                policy_holder=(
                    data.get("policy_holder")
                    or data.get("claimant_name")
                ),
                vehicle_registration=data.get(
                    "vehicle_registration"
                ),
                coverage_type=data.get("coverage_type"),
                policy_start_date=self._parse_date(
                    data.get("policy_start_date")
                ),
                policy_end_date=self._parse_date(
                    data.get("policy_end_date")
                ),
                deductible=self._parse_float(
                    data.get("deductible")
                ),
                coverage_limit=self._parse_float(
                    data.get("coverage_limit")
                ),
            )

        if document_type == "POLICE_REPORT":
            return PoliceReportDocument(
                report_number=data.get("police_report_number"),
                claim_id=data.get("claim_id") or document.claim_id,
                policy_number=data.get("policy_number"),
                incident_date=self._parse_date(
                    data.get("incident_date")
                ),
                incident_time=data.get("incident_time"),
                incident_location=data.get("incident_location"),
                police_station=data.get("police_station"),
                officer_name=data.get("officer_name"),
                incident_description=data.get(
                    "incident_description"
                ),
                vehicle_registration=data.get(
                    "vehicle_registration"
                ),
            )

        if document_type == "REPAIR_ESTIMATE":
            return RepairEstimateDocument(
                estimate_number=data.get("estimate_number"),
                claim_id=data.get("claim_id") or document.claim_id,
                policy_number=data.get("policy_number"),
                vehicle_registration=data.get(
                    "vehicle_registration"
                ),
                repair_date=self._parse_date(
                    data.get("repair_date")
                ),
                workshop_name=data.get("workshop_name"),
                total_estimated_cost=self._parse_float(
                    data.get("estimated_repair_cost")
                    or data.get("total_estimated_cost")
                ),
                parts_cost=self._parse_float(
                    data.get("parts_cost")
                ),
                labor_cost=self._parse_float(
                    data.get("labor_cost")
                ),
                repair_description=data.get(
                    "repair_description"
                ),
            )

        if document_type == "MEDICAL_BILL":
            return MedicalBillDocument(
                bill_number=data.get("bill_number"),
                claim_id=data.get("claim_id") or document.claim_id,
                policy_number=data.get("policy_number"),
                patient_name=data.get("patient_name"),
                hospital_name=data.get("hospital_name"),
                admission_date=self._parse_date(
                    data.get("admission_date")
                ),
                discharge_date=self._parse_date(
                    data.get("discharge_date")
                ),
                diagnosis=data.get("diagnosis"),
                treatment_description=data.get(
                    "treatment_description"
                ),
                total_bill_amount=self._parse_float(
                    data.get("total_bill_amount")
                ),
            )

        if document_type == "DAMAGE_PHOTO":
            return DamagePhotoDocument(
                claim_id=data.get("claim_id") or document.claim_id,
                vehicle_registration=data.get(
                    "vehicle_registration"
                ),
                photo_description=data.get(
                    "photo_description"
                ),
                damage_area=data.get("damage_area"),
                visible_damage=data.get("visible_damage"),
                estimated_severity=data.get(
                    "estimated_severity"
                ),
            )

        raise ValueError(
            f"Unsupported structured document type: "
            f"{document_type}"
        )