from mcp.server.mcpserver import MCPServer
from src.evaluation.damage_consistency_service import (
    DamageConsistencyService,
)
from src.evaluation.expense_consistency_service import (
    ExpenseConsistencyService,
)
from src.evaluation.invariant_evaluation_service import (
    InvariantEvaluationService,
)
from src.models.schemas import (
    ClaimFormDocument,
    DamagePhotoDocument,
    PoliceReportDocument,
    PolicyDocument,
    RepairEstimateDocument,
)


mcp = MCPServer("ClaimGuard Invariant Server")

invariant_service = InvariantEvaluationService()
expense_consistency_service = ExpenseConsistencyService()
damage_consistency_service = DamageConsistencyService()


@mcp.tool()
def check_vehicle_registration(
    claim_form: dict,
    policy: dict,
) -> dict:
    """
    Check vehicle registration consistency between
    the claim form and policy.
    """

    claim_form_model = ClaimFormDocument.model_validate(claim_form)
    policy_model = PolicyDocument.model_validate(policy)

    result = invariant_service.check_vehicle_registration(
        claim_form=claim_form_model,
        policy=policy_model,
    )

    return result.model_dump(mode="json")


@mcp.tool()
def check_vehicle_registration_against_police_report(
    claim_form: dict,
    police_report: dict,
) -> dict:
    """
    Check vehicle registration consistency between
    the claim form and police report.
    """

    claim_form_model = ClaimFormDocument.model_validate(claim_form)
    police_report_model = PoliceReportDocument.model_validate(
        police_report
    )

    result = (
        invariant_service
        .check_vehicle_registration_against_police_report(
            claim_form=claim_form_model,
            police_report=police_report_model,
        )
    )

    return result.model_dump(mode="json")


@mcp.tool()
def check_policy_number(
    claim_form: dict,
    policy: dict,
) -> dict:
    """
    Check policy number consistency between
    the claim form and policy.
    """

    claim_form_model = ClaimFormDocument.model_validate(claim_form)
    policy_model = PolicyDocument.model_validate(policy)

    result = invariant_service.check_policy_number(
        claim_form=claim_form_model,
        policy=policy_model,
    )

    return result.model_dump(mode="json")


@mcp.tool()
def check_incident_date(
    claim_form: dict,
    police_report: dict,
) -> dict:
    """
    Check incident date consistency between
    the claim form and police report.
    """

    claim_form_model = ClaimFormDocument.model_validate(claim_form)
    police_report_model = PoliceReportDocument.model_validate(
        police_report
    )

    result = invariant_service.check_incident_date(
        claim_form=claim_form_model,
        police_report=police_report_model,
    )

    return result.model_dump(mode="json")


@mcp.tool()
def check_claimant_name(
    claim_form: dict,
    policy: dict,
) -> dict:
    """
    Check claimant name consistency between
    the claim form and policy.
    """

    claim_form_model = ClaimFormDocument.model_validate(claim_form)
    policy_model = PolicyDocument.model_validate(policy)

    result = invariant_service.check_claimant_name(
        claim_form=claim_form_model,
        policy=policy_model,
    )

    return result.model_dump(mode="json")


@mcp.tool()
def validate_repair_estimate_consistency(repair_estimate: dict) -> dict:
    """
    Validate whether parts cost and labor cost sum to the total repair cost.
    """
    estimate_model = RepairEstimateDocument.model_validate(repair_estimate)
    result = expense_consistency_service.validate_repair_estimate(estimate_model)
    return result.model_dump(mode="json")


@mcp.tool()
def check_damage_area_consistency(
    claim_form: dict,
    damage_photo: dict,
) -> dict:
    """
    Validate whether damage photo observation matches the incident description.
    """
    claim_form_model = ClaimFormDocument.model_validate(claim_form)
    damage_photo_model = DamagePhotoDocument.model_validate(damage_photo)
    result = damage_consistency_service.compare_damage(
        claim_form=claim_form_model,
        damage_photo=damage_photo_model,
    )
    return result.model_dump(mode="json")


if __name__ == "__main__":
    mcp.run()