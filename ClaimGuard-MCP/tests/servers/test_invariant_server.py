import asyncio
import json

from src.servers.invariant_server import mcp


def call_tool(tool_name: str, arguments: dict) -> dict:
    result = asyncio.run(
        mcp.call_tool(tool_name, arguments)
    )

    assert result.is_error is False

    return json.loads(result.content[0].text)


def test_check_vehicle_registration_mcp():
    response = call_tool(
        "check_vehicle_registration",
        {
            "claim_form": {
                "claim_id": "MCP-TEST-001",
                "vehicle_registration": "GJ01AB1234",
            },
            "policy": {
                "policy_number": "POL-001",
                "vehicle_registration": "GJ01XY9999",
            },
        },
    )

    assert response["result"] == "FAIL"
    assert response["severity"] == "HIGH"
    assert response["invariant_id"] == (
        "VEHICLE_REGISTRATION_CONSISTENCY"
    )


def test_check_vehicle_registration_against_police_report_mcp():
    response = call_tool(
        "check_vehicle_registration_against_police_report",
        {
            "claim_form": {
                "claim_id": "MCP-TEST-002",
                "vehicle_registration": "GJ01AB1234",
            },
            "police_report": {
                "vehicle_registration": "GJ01XY9999",
            },
        },
    )

    assert response["result"] == "FAIL"
    assert response["severity"] == "HIGH"
    assert response["invariant_id"] == (
        "VEHICLE_REGISTRATION_POLICE_REPORT_CONSISTENCY"
    )


def test_check_policy_number_mcp():
    response = call_tool(
        "check_policy_number",
        {
            "claim_form": {
                "claim_id": "MCP-TEST-003",
                "policy_number": "POL-001",
            },
            "policy": {
                "policy_number": "POL-999",
            },
        },
    )

    assert response["result"] == "FAIL"
    assert response["severity"] == "HIGH"
    assert response["invariant_id"] == (
        "POLICY_NUMBER_CONSISTENCY"
    )


def test_check_incident_date_mcp():
    response = call_tool(
        "check_incident_date",
        {
            "claim_form": {
                "claim_id": "MCP-TEST-004",
                "incident_date": "2026-09-05",
            },
            "police_report": {
                "incident_date": "2026-09-06",
            },
        },
    )

    assert response["result"] == "FAIL"
    assert response["severity"] == "HIGH"
    assert response["invariant_id"] == (
        "INCIDENT_DATE_CONSISTENCY"
    )


def test_check_claimant_name_mcp():
    response = call_tool(
        "check_claimant_name",
        {
            "claim_form": {
                "claim_id": "MCP-TEST-005",
                "claimant_name": "Rahul Sharma",
            },
            "policy": {
                "policy_number": "POL-001",
                "policy_holder": "Amit Patel",
            },
        },
    )

    assert response["result"] == "FAIL"
    assert response["severity"] == "HIGH"
    assert response["invariant_id"] == (
        "CLAIMANT_NAME_CONSISTENCY"
    )