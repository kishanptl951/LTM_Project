from src.models.schemas import (
    PolicyDocument,
    ClaimFormDocument,
    PoliceReportDocument,
    RepairEstimateDocument,
    MedicalBillDocument,
    DamagePhotoDocument,
    StructuredDocument,
)


def test_policy_document():
    policy = PolicyDocument(
        policy_number="POL-2026-001",
        policy_holder="Rahul Sharma",
        vehicle_registration="TS09AB1234",
        coverage_type="Comprehensive",
        deductible=10000.0,
        coverage_limit=500000.0,
    )

    assert policy.policy_number == "POL-2026-001"
    assert policy.policy_holder == "Rahul Sharma"
    assert policy.vehicle_registration == "TS09AB1234"
    assert policy.coverage_type == "Comprehensive"
    assert policy.deductible == 10000.0
    assert policy.coverage_limit == 500000.0




def test_claim_form_document():
    claim = ClaimFormDocument(
        claim_id="CLM-001",
        policy_number="POL-2026-001",
        claimant_name="Rahul Sharma",
        claim_type="Motor Vehicle Accident",
        incident_date="2026-09-05",
        reported_date="2026-09-06",
        incident_location="Hyderabad, Telangana",
        incident_description="Front-end collision causing bumper and headlight damage.",
        vehicle_registration="TS09AB1234",
    )

    assert claim.claim_id == "CLM-001"
    assert claim.policy_number == "POL-2026-001"
    assert claim.claimant_name == "Rahul Sharma"
    assert claim.incident_date.isoformat() == "2026-09-05"
    assert claim.reported_date.isoformat() == "2026-09-06"
    assert claim.vehicle_registration == "TS09AB1234"

def test_police_report_document():
    report = PoliceReportDocument(
        report_number="HYD-2026-0915",
        claim_id="CLM-001",
        policy_number="POL-2026-001",
        incident_date="2026-09-05",
        incident_time="18:30",
        incident_location="Hyderabad, Telangana",
        police_station="Banjara Hills Police Station",
        officer_name="Inspector R. Kumar",
        incident_description="Vehicle collision reported with front-end damage.",
        vehicle_registration="TS09AB1234",
    )

    assert report.report_number == "HYD-2026-0915"
    assert report.claim_id == "CLM-001"
    assert report.policy_number == "POL-2026-001"
    assert report.incident_date.isoformat() == "2026-09-05"
    assert report.incident_location == "Hyderabad, Telangana"
    assert report.vehicle_registration == "TS09AB1234"

def test_repair_estimate_document():
    estimate = RepairEstimateDocument(
        estimate_number="EST-2026-001",
        claim_id="CLM-001",
        policy_number="POL-2026-001",
        vehicle_registration="TS09AB1234",
        repair_date="2026-09-08",
        workshop_name="Hyderabad Auto Works",
        total_estimated_cost=85000.0,
        parts_cost=60000.0,
        labor_cost=25000.0,
        repair_description="Front bumper and left headlight replacement.",
    )

    assert estimate.estimate_number == "EST-2026-001"
    assert estimate.claim_id == "CLM-001"
    assert estimate.policy_number == "POL-2026-001"
    assert estimate.vehicle_registration == "TS09AB1234"
    assert estimate.repair_date.isoformat() == "2026-09-08"
    assert estimate.total_estimated_cost == 85000.0
    assert estimate.parts_cost == 60000.0
    assert estimate.labor_cost == 25000.0

def test_medical_bill_document():
    bill = MedicalBillDocument(
        bill_number="MED-2026-001",
        claim_id="CLM-001",
        policy_number="POL-2026-001",
        patient_name="Rahul Sharma",
        hospital_name="Apollo Hospital Hyderabad",
        admission_date="2026-09-05",
        discharge_date="2026-09-07",
        diagnosis="Minor injuries following vehicle accident.",
        treatment_description="Emergency treatment and observation.",
        total_bill_amount=45000.0,
    )

    assert bill.bill_number == "MED-2026-001"
    assert bill.claim_id == "CLM-001"
    assert bill.patient_name == "Rahul Sharma"
    assert bill.hospital_name == "Apollo Hospital Hyderabad"
    assert bill.admission_date.isoformat() == "2026-09-05"
    assert bill.discharge_date.isoformat() == "2026-09-07"
    assert bill.total_bill_amount == 45000.0

def test_damage_photo_document():
    photo = DamagePhotoDocument(
        claim_id="CLM-001",
        vehicle_registration="TS09AB1234",
        photo_description="Front view of the damaged vehicle.",
        damage_area="Front bumper and left headlight",
        visible_damage="Cracked bumper and broken headlight.",
        estimated_severity="Moderate",
    )

    assert photo.claim_id == "CLM-001"
    assert photo.vehicle_registration == "TS09AB1234"
    assert photo.damage_area == "Front bumper and left headlight"
    assert photo.visible_damage == "Cracked bumper and broken headlight."
    assert photo.estimated_severity == "Moderate"

def test_structured_document():
    document = StructuredDocument(
        document_id="DOC-001",
        claim_id="CLM-001",
        document_type="CLAIM_FORM",
        extracted_data={
            "claim_id": "CLM-001",
            "policy_number": "POL-2026-001",
            "vehicle_registration": "TS09AB1234",
        },
        confidence=0.97,
    )

    assert document.document_id == "DOC-001"
    assert document.claim_id == "CLM-001"
    assert document.document_type == "CLAIM_FORM"
    assert document.extracted_data["policy_number"] == "POL-2026-001"
    assert document.confidence == 0.97