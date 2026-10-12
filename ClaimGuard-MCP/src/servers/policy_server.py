from mcp.server.mcpserver import MCPServer
from src.evaluation.policy_evaluation_service import PolicyEvaluationService
from src.models.schemas import Claim, PolicyDocument


mcp = MCPServer("ClaimGuard Policy Server")

policy_service = PolicyEvaluationService()


@mcp.tool()
def evaluate_claim_policy(
    claim: dict,
    policy: dict,
) -> list[dict]:
    """
    Evaluate an insurance claim against its policy.

    Checks policy period, policy number, and vehicle registration.

    Args:
        claim: Claim data matching the Claim schema.
        policy: Policy data matching the PolicyDocument schema.

    Returns:
        Policy evaluation results.
    """

    claim_model = Claim.model_validate(claim)
    policy_model = PolicyDocument.model_validate(policy)

    evaluations = policy_service.evaluate_claim(
        claim=claim_model,
        policy=policy_model,
    )

    return [
        evaluation.model_dump(mode="json")
        for evaluation in evaluations
    ]


if __name__ == "__main__":
    mcp.run()