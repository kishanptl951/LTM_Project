from mcp.server.mcpserver import MCPServer

from src.orchestration.claim_package_service import (
    ClaimPackageService,
)

from src.evaluation.claim_evaluation_pipeline import (
    ClaimEvaluationPipeline,
)
from src.models.schemas import (
    Claim,
    ClaimFormDocument,
    DamagePhotoDocument,
    PolicyDocument,
    PoliceReportDocument,
    RepairEstimateDocument,
)


mcp = MCPServer("ClaimGuard Claim Server")

pipeline = ClaimEvaluationPipeline()
package_service = ClaimPackageService()

@mcp.tool()
def assess_claim(
    claim: dict,
    policy: dict,
    claim_form: dict,
    police_report: dict | None = None,
    repair_estimate: dict | None = None,
    damage_photo: dict | None = None,
    evidence_count: int | None = None,
) -> dict:
    """
    Perform a complete claim assessment.

    Coordinates policy evaluation, document consistency checks,
    expense validation, damage consistency, required-document
    checks, and evidence assessment.
    """

    claim_model = Claim.model_validate(claim)

    policy_model = PolicyDocument.model_validate(policy)

    claim_form_model = ClaimFormDocument.model_validate(
        claim_form
    )

    police_report_model = (
        PoliceReportDocument.model_validate(police_report)
        if police_report is not None
        else None
    )

    repair_estimate_model = (
        RepairEstimateDocument.model_validate(repair_estimate)
        if repair_estimate is not None
        else None
    )

    damage_photo_model = (
        DamagePhotoDocument.model_validate(damage_photo)
        if damage_photo is not None
        else None
    )

    assessment = pipeline.evaluate_claim(
        claim=claim_model,
        policy=policy_model,
        claim_form=claim_form_model,
        police_report=police_report_model,
        repair_estimate=repair_estimate_model,
        damage_photo=damage_photo_model,
        evidence_count=evidence_count,
    )

    return assessment.model_dump(mode="json")

@mcp.tool()
def process_claim_package(
    package_path: str,
    claim_id: str,
) -> dict:
    """
    Process a complete insurance claim package.

    The package may contain claim PDFs and vehicle damage images.
    The existing ClaimPackageService performs document extraction,
    vision analysis, claim evaluation, and returns the final
    assessment.
    """

    assessment = package_service.process_package(
        package_path=package_path,
        claim_id=claim_id,
    )

    return assessment.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run()