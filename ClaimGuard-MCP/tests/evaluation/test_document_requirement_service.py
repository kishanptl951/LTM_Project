from src.evaluation.document_requirement_service import (
    DocumentRequirementService,
)
from src.models.schemas import Claim


def test_motor_claim_required_documents():

    claim = Claim(
        claim_id="TEST-DOC-001",
        policy_number="POL-001",
        claim_type="Motor Vehicle Accident",
    )

    service = DocumentRequirementService()

    required_documents = service.get_required_documents(claim)

    assert "CLAIM_FORM" in required_documents
    assert "POLICY" in required_documents
    assert "DAMAGE_PHOTO" in required_documents


def test_motor_claim_conditional_documents():

    claim = Claim(
        claim_id="TEST-DOC-002",
        policy_number="POL-001",
        claim_type="Motor Vehicle Accident",
    )

    service = DocumentRequirementService()

    conditional_documents = service.get_conditional_documents(claim)

    assert "POLICE_REPORT" in conditional_documents


def test_non_motor_claim_does_not_require_damage_photo():

    claim = Claim(
        claim_id="TEST-DOC-003",
        policy_number="POL-001",
        claim_type="Medical Claim",
    )

    service = DocumentRequirementService()

    required_documents = service.get_required_documents(claim)

    assert "CLAIM_FORM" in required_documents
    assert "POLICY" in required_documents
    assert "DAMAGE_PHOTO" not in required_documents


def test_non_motor_claim_has_no_police_report_requirement():

    claim = Claim(
        claim_id="TEST-DOC-004",
        policy_number="POL-001",
        claim_type="Medical Claim",
    )

    service = DocumentRequirementService()

    conditional_documents = service.get_conditional_documents(claim)

    assert "POLICE_REPORT" not in conditional_documents