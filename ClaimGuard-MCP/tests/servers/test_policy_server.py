import asyncio

from src.servers.policy_server import mcp


def call_tool(tool_name: str, arguments: dict) -> list[dict]:
    result = asyncio.run(
        mcp.call_tool(tool_name, arguments)
    )

    assert result.is_error is False
    assert result.structured_content is not None

    return result.structured_content["result"]


def test_evaluate_claim_policy_mcp():
    response = call_tool(
        "evaluate_claim_policy",
        {
            "claim": {
                "claim_id": "MCP-POL-001",
                "policy_number": "POL-001",
                "claimant_name": "Rahul Sharma",
                "claim_type": "Vehicle Damage",
                "incident_date": "2026-09-05",
                "reported_date": "2026-09-06",
                "vehicle_registration": "GJ01AB1234",
            },
            "policy": {
                "policy_number": "POL-001",
                "policy_holder": "Rahul Sharma",
                "vehicle_registration": "GJ01AB1234",
                "coverage_type": "Comprehensive",
                "policy_start_date": "2026-01-01",
                "policy_end_date": "2026-12-31",
                "deductible": 10000.0,
                "coverage_limit": 100000.0,
            },
        },
    )

    assert len(response) == 3

    results = {
        item["rule_id"]: item["result"]
        for item in response
    }

    assert results["POLICY_PERIOD"] == "PASS"
    assert results["POLICY_NUMBER_MATCH"] == "PASS"
    assert results["VEHICLE_REGISTRATION_MATCH"] == "PASS"