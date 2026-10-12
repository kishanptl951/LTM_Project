import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.servers.claim_server"],
        cwd=r"C:\Users\T9934\Desktop\ClaimGuard-MCP",
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            tools = await session.list_tools()

            print("Available MCP tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")
            assert "assess_claim" in [tool.name for tool in tools.tools]
            assert "process_claim_package" in [tool.name for tool in tools.tools]

            result = await session.call_tool(
                "assess_claim",
                arguments={
                    "claim": {
                        "claim_id": "CLM-MCP-001",
                        "policy_number": "POL-REAL-001",
                        "claimant_name": "Rahul Sharma",
                        "claim_type": "Motor Vehicle Accident",
                        "incident_date": "2026-09-05",
                        "reported_date": "2026-09-06",
                        "vehicle_registration": "TS09AB1234",
                        "status": "PENDING",
                    },
                    "policy": {
                        "policy_number": "POL-REAL-001",
                        "policy_holder": "Rahul Sharma",
                        "vehicle_registration": "TS09AB1234",
                        "coverage_type": "Comprehensive Motor Insurance",
                        "policy_start_date": "2026-01-01",
                        "policy_end_date": "2026-12-31",
                        "deductible": 5000,
                        "coverage_limit": 500000,
                    },
                    "claim_form": {
                        "claim_id": "CLM-MCP-001",
                        "policy_number": "POL-REAL-001",
                        "claimant_name": "Rahul Sharma",
                        "claim_type": "Motor Vehicle Accident",
                        "incident_date": "2026-09-05",
                        "reported_date": "2026-09-06",
                        "incident_location": "Hyderabad",
                        "incident_description": (
                            "The insured vehicle was involved in a road "
                            "accident. The front bumper and headlights "
                            "were damaged."
                        ),
                        "vehicle_registration": "TS09AB1234",
                    },
                    "police_report": {
                        "report_number": "PR-MCP-001",
                        "claim_id": "CLM-MCP-001",
                        "policy_number": "POL-REAL-001",
                        "incident_date": "2026-09-05",
                        "incident_time": "18:30",
                        "incident_location": "Hyderabad",
                        "police_station": "Banjara Hills Police Station",
                        "officer_name": "Arun Kumar",
                        "incident_description": (
                            "The insured vehicle was involved in a road "
                            "accident. The front bumper and headlights "
                            "were damaged."
                        ),
                        "vehicle_registration": "TS09AB1234",
                    },
                    "repair_estimate": {
                        "estimate_number": "EST-MCP-001",
                        "claim_id": "CLM-MCP-001",
                        "policy_number": "POL-REAL-001",
                        "vehicle_registration": "TS09AB1234",
                        "repair_date": "2026-09-08",
                        "workshop_name": "Hyderabad Auto Works",
                        "total_estimated_cost": 85000,
                        "parts_cost": 65000,
                        "labor_cost": 20000,
                        "repair_description": (
                            "Replacement of damaged front bumper "
                            "and headlights."
                        ),
                    },
                    "damage_photo": {
                        "claim_id": "CLM-MCP-001",
                        "vehicle_registration": "TS09AB1234",
                        "photo_description": (
                            "A vehicle with front-end damage."
                        ),
                        "damage_area": "front end",
                        "visible_damage": (
                            "damaged front bumper and headlights"
                        ),
                        "estimated_severity": "severe",
                    },
                },
            )

            print("\nMCP tool result:")
            print(result)


if __name__ == "__main__":
    asyncio.run(main())