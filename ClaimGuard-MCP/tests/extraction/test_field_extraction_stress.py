import pytest

from src.extraction.field_extraction_service import (
    FieldExtractionService,
)


@pytest.fixture
def extractor():
    return FieldExtractionService()


def extract_value(
    extractor,
    text,
    field_name,
):
    results = extractor.extract_fields(
        text=text,
        claim_id="STRESS-001",
        document_id="DOC-STRESS-001",
    )

    for result in results:
        if result.field_name == field_name:
            return result.field_value

    return None


# ============================================================
# POLICY NUMBER VARIATIONS
# ============================================================


def test_policy_number_standard_format(extractor):

    text = """
    Policy Number: POL-2026-001
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-001"
    )


def test_policy_number_no_abbreviation(extractor):

    text = """
    Policy No.: POL-2026-002
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-002"
    )


def test_policy_number_hash_format(extractor):

    text = """
    Policy #: POL-2026-003
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-003"
    )


def test_policy_number_next_line(extractor):

    text = """
    Policy Number:
    POL-2026-004
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-004"
    )


def test_policy_number_extra_spaces(extractor):

    text = """
    Policy Number   :     POL-2026-005
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-005"
    )


# ============================================================
# DATE VARIATIONS
# ============================================================


def test_incident_date_standard(extractor):

    text = """
    Incident Date: 2026-09-05
    """

    assert (
        extract_value(
            extractor,
            text,
            "incident_date",
        )
        == "2026-09-05"
    )


def test_incident_date_with_spaces(extractor):

    text = """
    Incident Date:    2026-09-05
    """

    assert (
        extract_value(
            extractor,
            text,
            "incident_date",
        )
        == "2026-09-05"
    )


def test_reported_date_standard(extractor):

    text = """
    Reported Date: 2026-09-06
    """

    assert (
        extract_value(
            extractor,
            text,
            "reported_date",
        )
        == "2026-09-06"
    )


# ============================================================
# VEHICLE REGISTRATION
# ============================================================


def test_vehicle_registration_standard(extractor):

    text = """
    Vehicle Registration: TS09AB1234
    """

    assert (
        extract_value(
            extractor,
            text,
            "vehicle_registration",
        )
        == "TS09AB1234"
    )


def test_vehicle_registration_extra_spaces(extractor):

    text = """
    Vehicle Registration:     TS09AB1234
    """

    assert (
        extract_value(
            extractor,
            text,
            "vehicle_registration",
        )
        == "TS09AB1234"
    )


# ============================================================
# MONEY VALUES
# ============================================================


def test_estimated_repair_cost_standard(extractor):

    text = """
    Estimated Repair Cost: 85000
    """

    assert (
        extract_value(
            extractor,
            text,
            "estimated_repair_cost",
        )
        == "85000"
    )


def test_estimated_repair_cost_with_currency(extractor):

    text = """
    Estimated Repair Cost: INR 85,000
    """

    assert (
        extract_value(
            extractor,
            text,
            "estimated_repair_cost",
        )
        == "INR 85,000"
    )


def test_parts_cost_standard(extractor):

    text = """
    Parts Cost: 60000
    """

    assert (
        extract_value(
            extractor,
            text,
            "parts_cost",
        )
        == "60000"
    )


def test_labor_cost_standard(extractor):

    text = """
    Labor Cost: 20000
    """

    assert (
        extract_value(
            extractor,
            text,
            "labor_cost",
        )
        == "20000"
    )


# ============================================================
# CASE INSENSITIVITY
# ============================================================


def test_policy_number_lowercase_label(extractor):

    text = """
    policy number: POL-2026-010
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-010"
    )


def test_vehicle_registration_mixed_case_label(extractor):

    text = """
    VeHiClE ReGiStRaTiOn: TS09AB1234
    """

    assert (
        extract_value(
            extractor,
            text,
            "vehicle_registration",
        )
        == "TS09AB1234"
    )


# ============================================================
# NOISE / REALISTIC DOCUMENT TEXT
# ============================================================


def test_policy_number_with_surrounding_document_text(extractor):

    text = """
    INSURANCE POLICY DOCUMENT

    Policy Number: POL-2026-011

    Policy Holder: Rahul Sharma

    Coverage Type: Comprehensive

    Policy Start Date: 2026-01-01
    Policy End Date: 2026-12-31

    Premium Amount: INR 24,500
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-011"
    )


def test_vehicle_registration_with_surrounding_text(extractor):

    text = """
    VEHICLE DETAILS

    Vehicle Make: Toyota
    Vehicle Model: Fortuner
    Vehicle Registration: TS09AB1234

    Incident Date: 2026-09-05
    """

    assert (
        extract_value(
            extractor,
            text,
            "vehicle_registration",
        )
        == "TS09AB1234"
    )


# ============================================================
# MISSING FIELD BEHAVIOR
# ============================================================


def test_missing_policy_number_returns_none(extractor):

    text = """
    Policy Holder: Rahul Sharma
    Coverage Type: Comprehensive
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        is None
    )


def test_missing_vehicle_registration_returns_none(extractor):

    text = """
    Vehicle Make: Toyota
    Vehicle Model: Fortuner
    """

    assert (
        extract_value(
            extractor,
            text,
            "vehicle_registration",
        )
        is None
    )


# ============================================================
# FIELD BOUNDARY TEST
# ============================================================


def test_policy_number_does_not_capture_next_field(extractor):

    text = """
    Policy Number: POL-2026-012
    Policy Holder: Rahul Sharma
    Coverage Type: Comprehensive
    """

    assert (
        extract_value(
            extractor,
            text,
            "policy_number",
        )
        == "POL-2026-012"
    )


def test_vehicle_registration_does_not_capture_next_field(
    extractor,
):

    text = """
    Vehicle Registration: TS09AB1234
    Vehicle Make: Toyota
    Vehicle Model: Fortuner
    """

    assert (
        extract_value(
            extractor,
            text,
            "vehicle_registration",
        )
        == "TS09AB1234"
    ) 