from pathlib import Path

import fitz

from src.extraction.claim_extraction_pipeline import ClaimExtractionPipeline


def create_pdf(path: Path, content: str) -> None:
    document = fitz.open()
    page = document.new_page()

    page.insert_text(
        (50, 50),
        content,
        fontsize=10,
    )

    document.save(path)
    document.close()


def test_realistic_claim_package(tmp_path):

    claim_id = "CLM-100"
    from src.db.session import get_db_connection

    with get_db_connection() as conn:

        conn.execute(
            """
            DELETE FROM extracted_evidence
            WHERE claim_id = ?
            """,
            [claim_id],
        )

    claim_form = tmp_path / "claim_form.pdf"
    policy = tmp_path / "policy.pdf"
    police_report = tmp_path / "police_report.pdf"
    repair_estimate = tmp_path / "repair_estimate.pdf"

    create_pdf(
        claim_form,
        """
MOTOR VEHICLE INSURANCE CLAIM FORM

Claim ID: CLM-100
Policy Number: POL-2026-100
Claimant Name: Rahul Sharma
Claim Type: Motor Vehicle Accident

Incident Date: 2026-09-05
Reported Date: 2026-09-06

Vehicle Registration: TS09AB1234
Vehicle Make: Toyota
Vehicle Model: Corolla

Damage Description:
Front bumper and left headlight damaged.

Estimated Repair Cost: INR 85,000
""",
    )

    create_pdf(
        policy,
        """
MOTOR INSURANCE POLICY

Policy Number: POL-2026-100
Claimant Name: Rahul Sharma

Vehicle Registration: TS09AB1234
Vehicle Make: Toyota
Vehicle Model: Corolla

Policy Start Date: 2026-01-01
Policy End Date: 2026-12-31
""",
    )

    create_pdf(
        police_report,
        """
POLICE ACCIDENT REPORT

Police Report Number: HYD-2026-100

Claim ID: CLM-100

Vehicle Registration: TS09AB1234

Incident Date: 2026-09-05

Location: Hyderabad, Telangana
""",
    )

    create_pdf(
        repair_estimate,
        """
VEHICLE REPAIR ESTIMATE

Vehicle Registration: TS09AB1234

Vehicle Make: Toyota
Vehicle Model: Corolla

Estimated Repair Cost: INR 85,000

Damage:
Front bumper replacement.
Left headlight replacement.
""",
    )

    pipeline = ClaimExtractionPipeline()

    documents = [
        claim_form,
        policy,
        police_report,
        repair_estimate,
    ]

    all_results = []

    for document in documents:
        result = pipeline.process_document(
            file_path=str(document),
            claim_id=claim_id,
            document_id=f"TEST-{document.stem.upper()}",
        )

        all_results.extend(result)

    extracted = {
        result.field_name: result.field_value
        for result in all_results
    }

    assert extracted["policy_number"] == "POL-2026-100"
    assert extracted["claimant_name"] == "Rahul Sharma"
    assert extracted["vehicle_registration"] == "TS09AB1234"
    assert extracted["vehicle_make"] == "Toyota"
    assert extracted["vehicle_model"] == "Corolla"

    assert len(all_results) >= 10