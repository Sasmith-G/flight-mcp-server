# 🔌 Flight MCP Server

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)

An open-source **Model Context Protocol (MCP) server** exposing real-time flight tracking, delay predictions, alternative flight searches, and passenger rights grounding (EU261, carrier rebooking policies) to AI assistants.

This repository serves as the interactive tool layer for **[flight-agent](https://github.com/Sasmith-G/flight-agent)** — allowing Claude Desktop, Cursor, and any MCP-compliant client to run flight disruption checks, alternative routing, and legal entitlement retrieval on demand.

---

## Exposed MCP Tools

| Tool Name | Description |
|---|---|
| `get_flight_status` | Query real-time operational status, departure/arrival schedules, and gate details. |
| `predict_flight_delay` | Retrieve predictive delay probabilities based on historical flight metrics. |
| `search_alternative_flights` | Search available rebooking options across operating carriers. |
| `retrieve_passenger_rights` | Lexical BM25 retrieval over EU261 regulations and duty-of-care policy documents. |
| `handle_disruption` | Execute the complete end-to-end disruption resolution flow on demand. |

---

## Quickstart

```bash
git clone [https://github.com/Sasmith-G/flight-mcp-server](https://github.com/Sasmith-G/flight-mcp-server)
cd flight-mcp-server
python -m venv .venv
.venv\Scripts\activate
pip install -e .
Integration with Claude Desktop
Add the following to your claude_desktop_config.json:

JSON
{
  "mcpServers": {
    "flight-mcp-server": {
      "command": "python",
      "args": ["-m", "amadeus_mcp_server.server"]
    }
  }
}
Related Projects
flight-agent — Autonomous background engine for flight disruption monitoring, RAG entitlement grounding, and proactive passenger notifications.