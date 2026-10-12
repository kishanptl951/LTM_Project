from src.extraction.field_extraction_service import FieldExtractionService


def test_standard_format():

    text = """
    Claim ID: CLM-001
    Policy Number: POL-2026-001
    Claimant Name: Rahul Sharma
    Vehicle Registration: TS09AB1234
    Incident Date: 2026-09-05
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-001",
        document_id="TEST-DOC-001",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["claim_id"] == "CLM-001"
    assert extracted["policy_number"] == "POL-2026-001"
    assert extracted["claimant_name"] == "Rahul Sharma"
    assert extracted["vehicle_registration"] == "TS09AB1234"
    assert extracted["incident_date"] == "2026-09-05"


def test_policy_number_without_colon():

    text = """
    Policy No. POL-2026-001
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-002",
        document_id="TEST-DOC-002",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted.get("policy_number") == "POL-2026-001"


def test_policy_number_with_hash():

    text = """
    Policy # POL-2026-001
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-003",
        document_id="TEST-DOC-003",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted.get("policy_number") == "POL-2026-001"


def test_policy_number_on_next_line():

    text = """
    Policy Number:
    POL-2026-001
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-004",
        document_id="TEST-DOC-004",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted.get("policy_number") == "POL-2026-001"


def test_vehicle_registration_with_extra_spaces():

    text = """
    Vehicle Registration:    TS09AB1234
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-005",
        document_id="TEST-DOC-005",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["vehicle_registration"] == "TS09AB1234"


def test_different_field_order():

    text = """
    Vehicle Registration: TS09AB1234
    Claimant Name: Rahul Sharma
    Policy Number: POL-2026-001
    Claim ID: CLM-006
    Incident Date: 2026-09-05
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-006",
        document_id="TEST-DOC-006",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["claim_id"] == "CLM-006"
    assert extracted["policy_number"] == "POL-2026-001"
    assert extracted["claimant_name"] == "Rahul Sharma"
    assert extracted["vehicle_registration"] == "TS09AB1234"
    assert extracted["incident_date"] == "2026-09-05"


def test_missing_optional_field_does_not_break_extraction():

    text = """
    Claim ID: CLM-007
    Policy Number: POL-2026-001
    Claimant Name: Rahul Sharma
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-007",
        document_id="TEST-DOC-007",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["claim_id"] == "CLM-007"
    assert extracted["policy_number"] == "POL-2026-001"
    assert extracted["claimant_name"] == "Rahul Sharma"

    assert "vehicle_registration" not in extracted


def test_real_claim_pdf_label_variations():
    """Verify extraction for all label variations and multi-column lines from real claim documents."""
    service = FieldExtractionService()

    # Document 1: Motor Insurance Claim Form snippet
    claim_form_text = """
    MOTOR INSURANCE CLAIM FORM
    CLAIM NO. AGS-CLM-2026-004381 POLICY NO. AGS-MOT-2026-018742
    A. INSURED DETAILS
    Insured Arjun Mehta Contact +91 98XX 41XX 72
    B. VEHICLE & LOSS DETAILS
    Registration No. GJ05TR4821 VIN MALHXX3E6RA000741
    Date of loss 14-Sep-2026 Time 18:35
    """

    results = service.extract_fields(
        text=claim_form_text,
        claim_id="AGS-CLM-2026-004381",
        document_id="DOC-CLAIM-FORM",
    )
    data = {r.field_name: r.field_value for r in results}

    assert data.get("policy_number") == "AGS-MOT-2026-018742"
    assert data.get("claimant_name") == "Arjun Mehta"
    assert data.get("vehicle_registration") == "GJ05TR4821"
    assert data.get("incident_date") == "14-Sep-2026"


def test_accident_report_label_variations():
    """Verify extraction from accident report with Complainant, Insurance policy, and Date."""
    service = FieldExtractionService()

    report_text = """
    ACCIDENT / INCIDENT REPORT
    1. COMPLAINANT / VEHICLE
    Complainant Arjun Mehta Vehicle No. GJ05TR4821
    Insurance policy AGS-MOT-2026-018742 Claim reference AGS-CLM-2026-004381
    2. INCIDENT PARTICULARS
    Date 14-Sep-2026 Approx. time 18:35
    """

    results = service.extract_fields(
        text=report_text,
        claim_id="AGS-CLM-2026-004381",
        document_id="DOC-POLICE-REPORT",
    )
    data = {r.field_name: r.field_value for r in results}

    assert data.get("policy_number") == "AGS-MOT-2026-018742"
    assert data.get("claimant_name") == "Arjun Mehta"
    assert data.get("vehicle_registration") == "GJ05TR4821"
    assert data.get("incident_date") == "14-Sep-2026"


def test_policy_schedule_label_variations():
    """Verify extraction from policy schedule with Policyholder, Loss date, and Registration No."""
    service = FieldExtractionService()

    schedule_text = """
    MOTOR INSURANCE POLICY SCHEDULE
    POLICY NUMBER AGS-MOT-2026-018742 STATUS ACTIVE (SYNTHETIC)
    1. POLICYHOLDER & INSURED VEHICLE
    Policyholder Arjun Mehta Mobile +91 98XX 41XX 72
    Vehicle Hyundai Verna 1.5 Turbo DCT Registration No. GJ05TR4821
    4. CLAIM REFERENCE
    Claim number AGS-CLM-2026-004381 Loss date 14-Sep-2026
    """

    results = service.extract_fields(
        text=schedule_text,
        claim_id="AGS-CLM-2026-004381",
        document_id="DOC-POLICY",
    )
    data = {r.field_name: r.field_value for r in results}

    assert data.get("policy_number") == "AGS-MOT-2026-018742"
    assert data.get("claimant_name") == "Arjun Mehta"
    assert data.get("vehicle_registration") == "GJ05TR4821"
    assert data.get("incident_date") == "14-Sep-2026"


def test_repair_invoice_and_estimate_labels():
    """Verify extraction from repair invoice and estimate with Bill To, Customer, Vehicle No."""
    service = FieldExtractionService()

    invoice_text = """
    PRIME LINE AUTOWORKS REPAIR INVOICE
    Bill To Arjun Mehta Vehicle No. GJ05TR4821
    Policy No. AGS-MOT-2026-018742 Claim No. AGS-CLM-2026-004381
    """

    results = service.extract_fields(
        text=invoice_text,
        claim_id="AGS-CLM-2026-004381",
        document_id="DOC-INVOICE",
    )
    data = {r.field_name: r.field_value for r in results}

    assert data.get("policy_number") == "AGS-MOT-2026-018742"
    assert data.get("claimant_name") == "Arjun Mehta"
    assert data.get("vehicle_registration") == "GJ05TR4821"

    estimate_text = """
    REPAIR ESTIMATE
    Customer Arjun Mehta Vehicle No. GJ05TR4821
    Policy No. AGS-MOT-2026-018742 Claim No. AGS-CLM-2026-004381
    """

    results_est = service.extract_fields(
        text=estimate_text,
        claim_id="AGS-CLM-2026-004381",
        document_id="DOC-ESTIMATE",
    )
    data_est = {r.field_name: r.field_value for r in results_est}

    assert data_est.get("policy_number") == "AGS-MOT-2026-018742"
    assert data_est.get("claimant_name") == "Arjun Mehta"
    assert data_est.get("vehicle_registration") == "GJ05TR4821"