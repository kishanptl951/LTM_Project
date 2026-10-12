from pathlib import Path

import pymupdf


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "sample_claims"
OUTPUT_FILE = OUTPUT_DIR / "sample_claim.pdf"


def create_sample_claim() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    document = pymupdf.open()

    page = document.new_page()

    claim_text = """
CLAIMGUARD-MCP — SAMPLE INSURANCE CLAIM

CLAIM DETAILS
Claim ID: CLM-001
Policy Number: POL-2026-001
Claimant Name: Rahul Sharma
Claim Type: Motor Vehicle Accident

INCIDENT DETAILS
Incident Date: 2026-09-05
Reported Date: 2026-09-06
Incident Location: Hyderabad, Telangana

VEHICLE DETAILS
Vehicle Registration: TS09AB1234
Vehicle Make: Toyota
Vehicle Model: Corolla
Vehicle Year: 2022

DAMAGE DETAILS
Damage: Front bumper and left headlight damaged.
Estimated Repair Cost: INR 85,000

POLICE REPORT
Police Report Number: HYD-2026-0915

DOCUMENT INFORMATION
Document Type: Accident Claim Form
Prepared By: Sample Insurance Department

This document is a synthetic test document created for the
ClaimGuard-MCP project. It does not represent a real insurance claim.
"""

    page.insert_text(
        (72, 72),
        claim_text.strip(),
        fontsize=12,
    )

    document.save(OUTPUT_FILE)
    document.close()

    print(f"Sample claim PDF created: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_sample_claim()