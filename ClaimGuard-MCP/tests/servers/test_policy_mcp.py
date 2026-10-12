import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.servers.policy_server"],
        cwd="C:\\Users\\T9934\\Desktop\\ClaimGuard-MCP",
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:

            await session.initialize()

            tools = await session.list_tools()

            print("Available MCP tools:")
            for tool in tools.tools:
                print(f"- {tool.name}")

            result = await session.call_tool(
                "evaluate_claim_policy",
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
                },
            )

            print("\nMCP tool result:")
            print(result)


if __name__ == "__main__":
    asyncio.run(main())