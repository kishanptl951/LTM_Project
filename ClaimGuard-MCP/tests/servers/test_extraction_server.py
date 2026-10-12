import asyncio
from pathlib import Path
from uuid import uuid4

from src.servers.extraction_server import mcp


def test_extract_claim_document_mcp():
    file_path = Path("data/sample_claims/sample_claim.pdf")

    assert file_path.exists()

    document_id = f"MCP-DOC-{uuid4().hex[:8]}"
    claim_id = f"MCP-EXT-{uuid4().hex[:8]}"

    result = asyncio.run(
        mcp.call_tool(
            "extract_claim_document",
            {
                "file_path": str(file_path),
                "claim_id": claim_id,
                "document_id": document_id,
            },
        )
    )

    assert result.is_error is False
    assert result.structured_content is not None

    evidence = result.structured_content["result"]

    assert isinstance(evidence, list)
    assert len(evidence) > 0

    field_names = {
        item["field_name"]
        for item in evidence
    }

    assert "claim_id" in field_names
    assert "policy_number" in field_names
    assert "claimant_name" in field_names

def test_extract_structured_document_mcp():

    file_path = Path("data/sample_claims/sample_claim.pdf")

    assert file_path.exists()

    document_id = f"MCP-STRUCT-{uuid4().hex[:8]}"
    claim_id = f"MCP-STRUCT-CLAIM-{uuid4().hex[:8]}"

    result = asyncio.run(
        mcp.call_tool(
            "extract_structured_document",
            {
                "file_path": str(file_path),
                "claim_id": claim_id,
                "document_id": document_id,
            },
        )
    )

    assert result.is_error is False
    assert result.content

    import json

    response = json.loads(result.content[0].text)

    assert response["document_type"] == "ClaimFormDocument"

    data = response["data"]

    assert data["claim_id"] == "CLM-001"
    assert data["policy_number"] == "POL-2026-001"
    assert data["claimant_name"] == "Rahul Sharma"
    assert data["claim_type"] == "Motor Vehicle Accident"
    assert data["incident_date"] == "2026-09-05"
    assert data["vehicle_registration"] == "TS09AB1234"