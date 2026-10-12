from src.extraction.field_extraction_service import FieldExtractionService


def test_lowercase_labels():

    text = """
    claim id: CLM-010
    policy number: POL-2026-010
    claimant name: Rahul Sharma
    vehicle registration: TS09AB1234
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-010",
        document_id="TEST-OCR-001",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["claim_id"] == "CLM-010"
    assert extracted["policy_number"] == "POL-2026-010"
    assert extracted["claimant_name"] == "Rahul Sharma"
    assert extracted["vehicle_registration"] == "TS09AB1234"


def test_extra_whitespace_in_labels():

    text = """
    Policy     Number:    POL-2026-011
    Claimant Name:     Rahul Sharma
    Vehicle Registration:       TS09AB1234
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-011",
        document_id="TEST-OCR-002",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["policy_number"] == "POL-2026-011"
    assert extracted["claimant_name"] == "Rahul Sharma"
    assert extracted["vehicle_registration"] == "TS09AB1234"


def test_field_value_with_trailing_whitespace():

    text = """
    Policy Number: POL-2026-012
    Claimant Name: Rahul Sharma
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-012",
        document_id="TEST-OCR-003",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["policy_number"] == "POL-2026-012"
    assert extracted["claimant_name"] == "Rahul Sharma"


def test_fields_with_mixed_case():

    text = """
    PoLiCy NuMbEr: POL-2026-013
    cLaImAnT nAmE: Rahul Sharma
    VeHiClE ReGiStRaTiOn: TS09AB1234
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-013",
        document_id="TEST-OCR-004",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["policy_number"] == "POL-2026-013"
    assert extracted["claimant_name"] == "Rahul Sharma"
    assert extracted["vehicle_registration"] == "TS09AB1234"


def test_value_on_next_line_with_spaces():

    text = """
    Policy Number:

    POL-2026-014

    Claimant Name:
    Rahul Sharma
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-014",
        document_id="TEST-OCR-005",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["policy_number"] == "POL-2026-014"
    assert extracted["claimant_name"] == "Rahul Sharma"