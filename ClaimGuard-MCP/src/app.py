from pathlib import Path
import argparse

from src.orchestration.claim_package_service import ClaimPackageService
from src.reporting import PDFReportService, ReportService
from src.utils import setup_logging


def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        description="ClaimGuard-MCP Insurance Claim Assessment"
    )

    parser.add_argument(
        "--package",
        required=True,
        help="Path to the claim package directory",
    )

    parser.add_argument(
        "--claim-id",
        required=True,
        help="Claim ID",
    )

    args = parser.parse_args()

    package_path = Path(args.package)

    if not package_path.exists():
        raise FileNotFoundError(
            f"Claim package not found: {package_path}"
        )

    if not package_path.is_dir():
        raise ValueError(
            f"Claim package must be a directory: {package_path}"
        )

    service = ClaimPackageService()

    assessment = service.process_package(
        package_path=str(package_path),
        claim_id=args.claim_id,
    )
    report_service = ReportService()
    report_path = Path("reports") / f"{assessment.claim_id}_report.txt"
    report_service.generate_text_report(
        assessment=assessment,
        output_path=str(report_path),
    )

    pdf_service = PDFReportService()
    pdf_path = Path("reports") / f"{assessment.claim_id}_report.pdf"
    pdf_service.generate_pdf_report(
        assessment=assessment,
        output_path=str(pdf_path),
    )

    print(f"\nText report saved to: {report_path}")
    print(f"PDF report saved to:  {pdf_path}")

    print("\n" + "=" * 60)
    print("CLAIMGUARD-MCP CLAIM ASSESSMENT")
    print("=" * 60)

    print(f"Claim ID: {assessment.claim_id}")
    print(f"Overall Result: {assessment.overall_result}")
    print(f"Evidence Count: {assessment.evidence_count}")

    print("\nPolicy Results:")
    for result in assessment.policy_results:
        print(
            f"  [{result.result}] "
            f"{result.rule_id}: "
            f"{result.explanation}"
        )

    print("\nInvariant Results:")
    for result in assessment.invariant_results:
        print(
            f"  [{result.result}] "
            f"{result.invariant_id}: "
            f"{result.explanation}"
        )

    print("\nExpense Results:")
    for result in assessment.expense_results:
        print(
            f"  [{result.result}] "
            f"{result.rule_id}: "
            f"{result.explanation}"
        )

    print("\nDamage Results:")
    for result in assessment.damage_results:
        print(
            f"  [{result.result}] "
            f"{result.invariant_id}: "
            f"{result.explanation}"
        )

    print("\nMissing Documents:")
    if assessment.missing_documents:
        for document in assessment.missing_documents:
            print(f"  - {document}")
    else:
        print("  None")

    print("\nReasons:")
    if assessment.reasons:
        for reason in assessment.reasons:
            print(f"  - {reason}")
    else:
        print("  None")

    print("=" * 60)


if __name__ == "__main__":
    main()