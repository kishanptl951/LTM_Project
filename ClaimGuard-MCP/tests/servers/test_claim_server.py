import asyncio

from src.servers.claim_server import mcp


def call_tool(arguments: dict) -> dict:
    result = asyncio.run(
        mcp.call_tool(
            "assess_claim",
            arguments,
        )
    )

    assert result.is_error is False
    assert result.content

    return __import__("json").loads(result.content[0].text)


def test_assess_claim_mcp_pass():

    response = call_tool(
        {
            "claim": {
                "claim_id": "MCP-CLAIM-001",
                "policy_number": "POL-001",
                "claimant_name": "Rahul Sharma",
                "claim_type": None,
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
            "claim_form": {
                "claim_id": "MCP-CLAIM-001",
                "policy_number": "POL-001",
                "claimant_name": "Rahul Sharma",
                "incident_date": "2026-09-05",
                "vehicle_registration": "GJ01AB1234",
            },
            "police_report": {
                "claim_id": "MCP-CLAIM-001",
                "policy_number": "POL-001",
                "incident_date": "2026-09-05",
                "vehicle_registration": "GJ01AB1234",
            },
            "evidence_count": 5,
        }
    )

    assert response["claim_id"] == "MCP-CLAIM-001"
    assert response["overall_result"] == "PASS"
    assert response["evidence_count"] == 5

    assert len(response["policy_results"]) == 3
    assert len(response["invariant_results"]) == 5
    assert response["reasons"] == []


def test_assess_claim_mcp_review_on_vehicle_mismatch():

    response = call_tool(
        {
            "claim": {
                "claim_id": "MCP-CLAIM-002",
                "policy_number": "POL-001",
                "claimant_name": "Rahul Sharma",
                "claim_type": None,
                "incident_date": "2026-09-05",
                "vehicle_registration": "GJ01AB9999",
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
            "claim_form": {
                "claim_id": "MCP-CLAIM-002",
                "policy_number": "POL-001",
                "claimant_name": "Rahul Sharma",
                "incident_date": "2026-09-05",
                "vehicle_registration": "GJ01AB9999",
            },
            "police_report": {
                "claim_id": "MCP-CLAIM-002",
                "policy_number": "POL-001",
                "incident_date": "2026-09-05",
                "vehicle_registration": "GJ01AB9999",
            },
        }
    )

    assert response["claim_id"] == "MCP-CLAIM-002"
    assert response["overall_result"] in {"FAIL", "REVIEW"}

    assert len(response["reasons"]) >= 2

    assert any(
        "vehicle" in reason.lower()
        for reason in response["reasons"]
    )