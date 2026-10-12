"""Verification script to test field extraction across real claim documents."""
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.extraction.field_extraction_service import FieldExtractionService


def run_verification():
    service = FieldExtractionService()

    sample_claim_form = """
    AegisSure General Insurance Ltd. Motor Claim Form
    SAMPLE / DEMO DOCUMENT — NOT A VALID INSURANCE, POLICE OR TAX RECORD Page 1
    MOTOR INSURANCE CLAIM FORM
    Own Damage Claim • Preliminary Notification & Loss Details
    CLAIM NO. AGS-CLM-2026-004381 POLICY NO. AGS-MOT-2026-018742
    A. INSURED DETAILS
    Insured Arjun Mehta Contact +91 98XX 41XX 72
    Address 18, Shantivan Residency, Satellite,
    Ahmedabad, Gujarat 380015
    Email arjun.mehta@example.invalid
    Policy period 01-Apr-2026 – 31-Mar-2027 Vehicle Hyundai Verna 1.5 Turbo DCT
    B. VEHICLE & LOSS DETAILS
    Registration No. GJ05TR4821 VIN MALHXX3E6RA000741
    Date of loss 14-Sep-2026 Time 18:35
    Place of loss S.G. Highway service road, near Iskcon
    Cross Road, Ahmedabad
    Odometer 38,412 km
    Type of loss Accidental damage Third party No injury reported
    C. ACCIDENT DESCRIPTION
    Front-left impact with a roadside concrete divider while avoiding a sudden lane obstruction.
    """

    results = service.extract_fields(
        text=sample_claim_form,
        claim_id="AGS-CLM-2026-004381",
        document_id="DOC-CLAIM-FORM",
    )

    data = {r.field_name: r.field_value for r in results}

    print("=" * 60)
    print("CLAIMGUARD-MCP FIELD EXTRACTION VERIFICATION REPORT")
    print("=" * 60)

    expected = {
        "policy_number": "AGS-MOT-2026-018742",
        "vehicle_registration": "GJ05TR4821",
        "incident_date": "14-Sep-2026",
        "claimant_name": "Arjun Mehta",
    }

    all_passed = True
    for field, expected_val in expected.items():
        actual_val = data.get(field)
        status = "PASS" if actual_val == expected_val else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"[{status}] {field:<22} -> Expected: {expected_val:<20} | Actual: {actual_val}")

    print("=" * 60)
    if all_passed:
        print("ALL TARGET FIELDS EXTRACTED SUCCESSFULLY!")
    else:
        print("EXTRACTION MISMATCH DETECTED!")
    print("=" * 60)

    return all_passed


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
