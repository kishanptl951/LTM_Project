from src.extraction.field_extraction_service import FieldExtractionService


def test_duplicate_policy_number():

    text = """
    INSURANCE CLAIM DOCUMENT

    Policy Number: POL-2026-030

    Previous policy reference:
    Policy Number: POL-2025-999

    Claim ID: CLM-030
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-030",
        document_id="TEST-AMB-001",
    )

    policy_results = [
        result
        for result in results
        if result.field_name == "policy_number"
    ]

    # Current extractor uses the first matching value.
    assert len(policy_results) == 1
    assert policy_results[0].field_value == "POL-2026-030"


def test_multiple_numbers_near_policy_label():

    text = """
    Policy Number: POL-2026-031
    Customer Reference: REF-88421
    Transaction Number: TXN-99182
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-031",
        document_id="TEST-AMB-002",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["policy_number"] == "POL-2026-031"


def test_policy_label_without_value():

    text = """
    Claim ID: CLM-032
    Policy Number:
    Claimant Name: Rahul Sharma
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-032",
        document_id="TEST-AMB-003",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert "policy_number" not in extracted
    assert extracted["claimant_name"] == "Rahul Sharma"


def test_partial_vehicle_registration():

    text = """
    Claim ID: CLM-033
    Vehicle Registration: TS09
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-033",
        document_id="TEST-AMB-004",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    # Extraction should preserve the observed value.
    # Validation of whether it is a valid registration belongs
    # to a later validation/business-rule layer.
    assert extracted["vehicle_registration"] == "TS09"


def test_field_inside_longer_sentence():

    text = """
    The customer submitted the following information.
    Policy Number: POL-2026-034
    This policy covers the insured vehicle.
    Vehicle Registration: TS09AB1234
    The reported damage involves the front bumper.
    """

    service = FieldExtractionService()

    results = service.extract_fields(
        text=text,
        claim_id="CLM-034",
        document_id="TEST-AMB-005",
    )

    extracted = {
        result.field_name: result.field_value
        for result in results
    }

    assert extracted["policy_number"] == "POL-2026-034"
    assert extracted["vehicle_registration"] == "TS09AB1234"