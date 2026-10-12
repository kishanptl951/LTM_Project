
import re
from typing import Any

from src.models.schemas import ExtractedEvidence
from src.services.evidence_service import EvidenceService


class FieldExtractionService:

    def __init__(self) -> None:
        self.evidence_service = EvidenceService()

    FIELD_PATTERNS = {
        "claim_id": (
            r"(?:Claim\s*(?:ID|Number|No\.?|#))\s*:\s*(.+)"
        ),

        # Policy numbers are handled separately in extract_fields().
        "policy_number": r"(?!)",

        
       
        "claimant_name": (
            r"^[ \t]*(?:Claimant(?:[ \t]+Name)?|"
            r"Name[ \t]+of[ \t]+Claimant|"
            r"Insured(?:[ \t]+Name|[ \t]+Person)?|"
            r"Name[ \t]+of[ \t]+Insured|"
            r"Policyholder|Complainant|Customer|Bill[ \t]+To)"
            r"[ \t]*:?[ \t]*"
            r"(?:\r?\n[ \t]*\r?\n?[ \t]*)?"
            r"([\u0900-\u097F A-Za-z][\u0900-\u097F A-Za-z.'-]*"
            r"(?:[ \t]+[\u0900-\u097F A-Za-z][\u0900-\u097F A-Za-z.'-]*)*)"
            r"(?=[ \t]+(?:Contact|Mobile|Email|Vehicle|VIN|Address|Phone|"
            r"Odometer|Job|Claim|Date|Reg|Policy)\b|[ \t]*\r?$)"
        ),



        "policy_holder": (
            r"(?:Policy\s*Holder|Insured\s*Person|Policyholder)"
            r"\s*:\s*([^\r\n]+)"
        ),

        "coverage_type": (
            r"(?:Coverage\s*Type|Plan\s*Type|Type\s*of\s*Coverage)"
            r"\s*:\s*(.+)"
        ),

        "claim_type": (
            r"(?:Claim\s*Type|Nature\s*of\s*Claim)\s*:\s*(.+)"
        ),

        "incident_date": (
            r"(?:Incident\s*Date|Date\s*of\s*(?:Loss|Accident|Incident)|"
            r"Loss\s*Date|Accident\s*Date|Date(?:\s*of\s*Occurrence)?)"
            r"[ \t]*:?[ \t]*"
            r"([0-9]{1,2}[-/ ][A-Za-z]{3,9}[-/ ][0-9]{2,4}|"
            r"[0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}|"
            r"[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})"
        ),

        "reported_date": (
            r"(?:Reported\s*Date|Date\s*(?:Reported|of\s*Intimation))"
            r"\s*:\s*(.+)"
        ),

        "policy_start_date": (
            r"(?:Policy\s*Start\s*Date|Effective\s*Date|From\s*Date)"
            r"\s*:\s*(.+)"
        ),

        "policy_end_date": (
            r"(?:Policy\s*End\s*Date|Expiry\s*Date|To\s*Date)"
            r"\s*:\s*(.+)"
        ),

        # Reg cannot match the beginning of Registration.
        # Short observed values such as TS09 are preserved.
        "vehicle_registration": (
            r"(?:Vehicle[ \t]*(?:Registration(?:[ \t]*Number)?|"
            r"Reg(?:istration)?\.?|No\.?(?![A-Za-z]))|"
            r"Registration[ \t]*(?:No\.?(?![A-Za-z])|#|Number)?|"
            r"Reg(?:istration)?\.?[ \t]*No\.?|"
            r"Plate[ \t]*(?:No\.?|Number))"
            r"[ \t]*:?[ \t]*"
            r"([A-Za-z]{2}[ \t]*[-–—]?[ \t]*[0-9]{1,2}"
            r"[ \t]*[-–—]?[ \t]*[A-Za-z]{0,3}"
            r"[ \t]*[-–—]?[ \t]*[0-9]{4}|[A-Za-z0-9]{1,12})"
        ),

        "vehicle_make": (
            r"Vehicle\s*Make\s*:\s*(.+)"
        ),

        "vehicle_model": (
            r"Vehicle\s*Model\s*:\s*(.+)"
        ),

        "police_report_number": (
            r"(?:Police\s*Report\s*Number|Report\s*Number|"
            r"FIR\s*(?:Number|No\.?))\s*:\s*(.+)"
        ),

        "incident_time": (
            r"(?:Incident\s*Time|Time\s*of\s*(?:Loss|Accident))"
            r"\s*:\s*(.+)"
        ),

        "incident_location": (
            r"(?:Incident\s*Location|Place\s*of\s*(?:Loss|Accident))"
            r"\s*:\s*(.+)"
        ),

        "police_station": (
            r"Police\s*Station\s*:\s*(.+)"
        ),

        "officer_name": (
            r"(?:Officer\s*Name|Investigating\s*Officer)\s*:\s*(.+)"
        ),

        "estimate_number": (
            r"(?:Estimate\s*Number|Estimate\s*No\.?|Quote\s*No\.?)"
            r"\s*:\s*(.+)"
        ),

        "repair_date": (
            r"(?:Repair\s*Date|Date\s*of\s*Estimate)\s*:\s*(.+)"
        ),

        "workshop_name": (
            r"(?:Workshop\s*Name|Garage\s*Name|Repairer)\s*:\s*(.+)"
        ),

        "estimated_repair_cost": (
            r"(?:Estimated\s*Repair\s*Cost|Repair\s*Cost|"
            r"Total\s*(?:Estimated\s*)?Cost|Total\s*Estimate)"
            r"\s*:\s*(.+)"
        ),

        "parts_cost": (
            r"(?:Parts\s*Cost|Total\s*Parts|Cost\s*of\s*Parts)"
            r"\s*:\s*(.+)"
        ),

        "labor_cost": (
            r"(?:Labor\s*Cost|Labor\s*Charges|"
            r"Labour\s*(?:Cost|Charges))\s*:\s*(.+)"
        ),

        "deductible": (
            r"(?:Deductible|Excess)\s*:\s*(.+)"
        ),

        "coverage_limit": (
            r"(?:Coverage\s*Limit|Sum\s*Insured|Limit\s*of\s*Liability)"
            r"\s*:\s*(.+)"
        ),
    }

    def extract_fields(
        self,
        text: str,
        claim_id: str,
        document_id: str,
        page_number: int | None = None,
    ) -> list[ExtractedEvidence]:

        results = []

        for field_name, pattern in self.FIELD_PATTERNS.items():

            if field_name == "policy_number":
                match = None

                policy_label = re.compile(
                    r"(?<![A-Za-z])"
                    r"(?:Policy[ \t]*(?:Number|No\.?|#)|"
                    r"Insurance[ \t]+Policy)"
                    r"(?![A-Za-z])",
                    re.IGNORECASE,
                )

                for label_match in policy_label.finditer(text):
                    line_end = text.find("\n", label_match.end())

                    if line_end == -1:
                        line_end = len(text)

                    # First, check for a value on the same line.
                    same_line = text[label_match.end():line_end]

                    value_match = re.match(
                        r"[ \t]*:?[ \t]*"
                        r"([A-Za-z0-9]+(?:[-_/][A-Za-z0-9]+)*)",
                        same_line,
                    )

                    if (
                        value_match
                        and any(char.isdigit() for char in value_match.group(1))
                    ):
                        policy_value = value_match.group(1)

                        evidence_text = (
                            text[label_match.start():label_match.end()]
                            + same_line[:value_match.end()]
                        ).strip()

                        class PolicyMatch:
                            def __init__(self, evidence: str, value: str):
                                self.evidence = evidence
                                self.value = value

                            def group(self, number: int) -> str:
                                if number == 1:
                                    return self.value
                                return self.evidence

                        match = PolicyMatch(evidence_text, policy_value)
                        break

                    # If the label is empty, check only the first
                    # non-empty line after it. Do not skip another field.
                    following_text = (
                        text[line_end + 1:]
                        if line_end < len(text)
                        else ""
                    )

                    next_line = next(
                        (
                            line.strip()
                            for line in following_text.splitlines()
                            if line.strip()
                        ),
                        None,
                    )

                    if next_line:
                        next_value_match = re.match(
                            r"([A-Za-z0-9]+(?:[-_/][A-Za-z0-9]+)*)",
                            next_line,
                        )

                        if (
                            next_value_match
                            and any(
                                char.isdigit()
                                for char in next_value_match.group(1)
                            )
                        ):
                            policy_value = next_value_match.group(1)

                            class PolicyMatch:
                                def __init__(self, evidence: str, value: str):
                                    self.evidence = evidence
                                    self.value = value

                                def group(self, number: int) -> str:
                                    if number == 1:
                                        return self.value
                                    return self.evidence

                            match = PolicyMatch(
                                text[label_match.start():label_match.end()]
                                + "\n"
                                + policy_value,
                                policy_value,
                            )
                            break

            else:
                match = re.search(
                    pattern,
                    text,
                    re.IGNORECASE | re.MULTILINE,
                )

            if match:
                field_value = match.group(1).strip()

                # Reject a policy value that is actually a field label.
                if field_name == "policy_number":
                    if re.match(
                        r"^[A-Za-z][A-Za-z ]*:",
                        field_value,
                    ):
                        continue

                page_tag = (
                    f"p{page_number}-"
                    if page_number is not None
                    else ""
                )

                evidence = ExtractedEvidence(
                    evidence_id=(
                        f"{document_id}-{page_tag}{field_name}"
                    ),
                    claim_id=claim_id,
                    document_id=document_id,
                    field_name=field_name,
                    field_value=field_value,
                    confidence=1.0,
                    page_number=page_number,
                    evidence_text=match.group(0).strip(),
                )

                results.append(evidence)

        # Incident descriptions can span multiple lines.
        incident_description_pattern = (
            r"Incident Description:\s*(.*?)"
            r"(?=\n[A-Za-z][A-Za-z ]*:\s|\Z)"
        )

        description_match = re.search(
            incident_description_pattern,
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if description_match:
            description = description_match.group(1).strip()

            if description:
                evidence = ExtractedEvidence(
                    evidence_id=f"{document_id}-incident_description",
                    claim_id=claim_id,
                    document_id=document_id,
                    field_name="incident_description",
                    field_value=description,
                    confidence=1.0,
                    page_number=page_number,
                    evidence_text=description_match.group(0).strip(),
                )

                results.append(evidence)

        # Repair descriptions can span multiple lines.
        repair_description_pattern = (
            r"Repair Description:\s*(.*?)"
            r"(?=\n[A-Za-z][A-Za-z ]*:\s|\Z)"
        )

        repair_description_match = re.search(
            repair_description_pattern,
            text,
            re.IGNORECASE | re.DOTALL,
        )

        if repair_description_match:
            repair_description = (
                repair_description_match.group(1).strip()
            )

            if repair_description:
                evidence = ExtractedEvidence(
                    evidence_id=f"{document_id}-repair_description",
                    claim_id=claim_id,
                    document_id=document_id,
                    field_name="repair_description",
                    field_value=repair_description,
                    confidence=1.0,
                    page_number=page_number,
                    evidence_text=repair_description_match.group(0).strip(),
                )

                results.append(evidence)

        return results

    def extract_and_save_fields(
        self,
        text: str,
        claim_id: str,
        document_id: str,
        page_number: int | None = None,
    ) -> list[ExtractedEvidence]:

        results = self.extract_fields(
            text=text,
            claim_id=claim_id,
            document_id=document_id,
            page_number=page_number,
        )

        for evidence in results:
            self.evidence_service.save_evidence(evidence)

        return results

    def extract_fields_with_llm_fallback(
        self,
        text: str,
        claim_id: str,
        document_id: str,
        page_number: int | None = None,
        llm_service: Any = None,
    ) -> list[ExtractedEvidence]:
        """
        Two-tier extraction:
        1. Extract fields using regex patterns.
        2. If critical fields are missing, optionally use the LLM fallback.
        """

        results = self.extract_fields(
            text=text,
            claim_id=claim_id,
            document_id=document_id,
            page_number=page_number,
        )

        found_fields = {
            evidence.field_name: evidence.field_value
            for evidence in results
            if evidence.field_value
        }

        critical_fields = [
            "policy_number",
            "incident_date",
            "vehicle_registration",
        ]

        missing_critical = [
            field
            for field in critical_fields
            if not found_fields.get(field)
        ]

        if missing_critical:
            from src.extraction.llm_extraction_service import (
                LLMExtractionService,
            )

            service = llm_service or LLMExtractionService()

            if service.is_available():
                llm_data = service.extract_fields(
                    text=text,
                    missing_fields=missing_critical,
                )

                page_tag = (
                    f"p{page_number}-"
                    if page_number is not None
                    else ""
                )

                for field_name, field_value in llm_data.items():
                    if (
                        field_value is not None
                        and str(field_value).strip()
                        and not found_fields.get(field_name)
                    ):
                        clean_value = str(field_value).strip()
                        found_fields[field_name] = clean_value

                        results.append(
                            ExtractedEvidence(
                                evidence_id=(
                                    f"{document_id}-{page_tag}{field_name}"
                                ),
                                claim_id=claim_id,
                                document_id=document_id,
                                field_name=field_name,
                                field_value=clean_value,
                                confidence=0.85,
                                page_number=page_number,
                                evidence_text=(
                                    f"[Tier-2 LLM Fallback: {field_name}]"
                                ),
                            )
                        )

        return results
