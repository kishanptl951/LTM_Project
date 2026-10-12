from src.extraction.field_extraction_service import FieldExtractionService


def test_realistic_claim_form():

    text = """
    MOTOR INSURANCE CLAIM FORM

    Claim ID: CLM-020

    Policy No. POL-2026-020

    The insured person is Rahul Sharma.

    Vehicle Registration: TS09AB1234
    Vehicle Make: Toyota
    Vehicle Model: Corolla

    The accident occurred on 05/09/2026.
    Reported Date: 06/09/2026

    Police Report Number: HYD-2026-0920

    Estimated Repair Cost: INR 85,000
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-020",
        document_id="TEST-REALISTIC-001",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["claim_id"] == "CLM-020"
    assert extracted["policy_number"] == "POL-2026-020"
    assert extracted["vehicle_registration"] == "TS09AB1234"
    assert extracted["vehicle_make"] == "Toyota"
    assert extracted["vehicle_model"] == "Corolla"
    assert extracted["reported_date"] == "06/09/2026"
    assert extracted["police_report_number"] == "HYD-2026-0920"
    assert extracted["estimated_repair_cost"] == "INR 85,000"


def test_realistic_policy_document():

    text = """
    MOTOR INSURANCE POLICY DOCUMENT

    Policy Number: POL-2026-021

    Policyholder: Rahul Sharma

    Vehicle Registration: TS09AB1234

    Vehicle Make: Toyota
    Vehicle Model: Corolla

    Coverage Type: Comprehensive

    Policy Start Date: 01/01/2026
    Policy End Date: 31/12/2026
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-021",
        document_id="TEST-REALISTIC-002",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["policy_number"] == "POL-2026-021"
    assert extracted["vehicle_registration"] == "TS09AB1234"
    assert extracted["vehicle_make"] == "Toyota"
    assert extracted["vehicle_model"] == "Corolla"


def test_realistic_police_report():

    text = """
    POLICE ACCIDENT REPORT

    Police Report Number: HYD-2026-0922

    Claim ID: CLM-022

    Vehicle Registration: TS09AB1234

    Incident Date: 05/09/2026

    The vehicle was involved in a road traffic accident.
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-022",
        document_id="TEST-REALISTIC-003",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["police_report_number"] == "HYD-2026-0922"
    assert extracted["claim_id"] == "CLM-022"
    assert extracted["vehicle_registration"] == "TS09AB1234"
    assert extracted["incident_date"] == "05/09/2026"


def test_unrelated_text_does_not_create_fields():

    text = """
    Vehicle accident reported near Hyderabad.

    The driver stated that the front bumper was damaged.
    Estimated damage may require significant repair.

    No policy details were provided in this document.
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-023",
        document_id="TEST-REALISTIC-004",
    )

    assert results == []