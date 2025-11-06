"""The MCP server must register exactly the five documented tools with schemas."""

import pytest

from amadeus_mcp_server.server import mcp

EXPECTED_TOOLS = {
    "flight_status",
    "predict_delay",
    "search_flights",
    "passenger_rights",
    "handle_disruption",
}


@pytest.mark.asyncio
async def test_all_tools_registered_with_descriptions():
    tools = await mcp.list_tools()
    by_name = {t.name: t for t in tools}
    assert set(by_name) == EXPECTED_TOOLS
    for tool in tools:
        assert tool.description, f"{tool.name} is missing a description"
        assert tool.inputSchema.get("properties"), f"{tool.name} is missing an input schema"


@pytest.mark.asyncio
async def test_tool_call_over_mcp_protocol():
    result = await mcp.call_tool(
        "flight_status",
        {"carrier_code": "AF", "flight_number": "1234", "departure_date": "2026-07-10"},
    )
    text = str(result)
    assert "AF1234" in text
