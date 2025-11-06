"""MCP server exposing the Amadeus Self-Service APIs as tools.

Five tools, all backed by the `disruption_agent` package (github.com/Thaynabarreiro/
amadeus-disruption-agent), so mock/live behaviour, response normalisation and the
policy corpus stay in one place:

  * flight_status         — On-Demand Flight Status
  * predict_delay         — Flight Delay Prediction (P(delay > 2h))
  * search_flights        — Flight Offers Search
  * passenger_rights      — RAG over EU261 + carrier policies (cited sources)
  * handle_disruption     — runs the full disruption-agent LangGraph pipeline

Set AGENT_MODE=live plus Amadeus credentials in the environment for real data;
the default mock mode replays realistic fixtures so any MCP client can try the
server with zero credentials.
"""

from __future__ import annotations

from datetime import date, datetime

from disruption_agent.agent import run_agent
from disruption_agent.amadeus import get_client
from disruption_agent.config import get_settings
from disruption_agent.rag import PolicyRetriever
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "amadeus",
    instructions=(
        "Tools over the Amadeus Self-Service APIs: check flight status, predict delays, "
        "search flights, look up passenger rights (EU261/carrier policy, with sources), "
        "and run an end-to-end disruption-handling agent."
    ),
)


def _client():
    return get_client()


def _retriever() -> PolicyRetriever:
    return PolicyRetriever(get_settings().resolved_fare_rules_dir)


@mcp.tool()
def flight_status(carrier_code: str, flight_number: str, departure_date: str) -> dict:
    """Get the status of a flight (scheduled vs estimated times, delay, cancellation).

    Args:
        carrier_code: IATA carrier code, e.g. "AF".
        flight_number: Flight number without carrier, e.g. "1234".
        departure_date: Scheduled departure date, ISO format "YYYY-MM-DD".
    """
    status = _client().flight_status(
        carrier_code, flight_number, date.fromisoformat(departure_date)
    )
    if status is None:
        return {"found": False, "message": "Flight not found in schedules."}
    return {
        "found": True,
        "flight": status.flight_designator,
        "route": f"{status.departure_iata}->{status.arrival_iata}",
        "scheduled_departure": status.scheduled_departure.isoformat(),
        "estimated_departure": (
            status.estimated_departure.isoformat() if status.estimated_departure else None
        ),
        "delay_minutes": status.delay_minutes,
        "cancelled": status.cancelled,
    }


@mcp.tool()
def predict_delay(
    origin: str, destination: str, departure_datetime: str, carrier_code: str, flight_number: str
) -> dict:
    """Predict the probability that a flight is delayed by more than 2 hours.

    Args:
        origin: Origin IATA airport code, e.g. "NCE".
        destination: Destination IATA airport code, e.g. "CDG".
        departure_datetime: Scheduled departure, ISO format "YYYY-MM-DDTHH:MM".
        carrier_code: IATA carrier code, e.g. "AF".
        flight_number: Flight number, e.g. "1234".
    """
    probability = _client().delay_prediction(
        origin, destination, datetime.fromisoformat(departure_datetime), carrier_code, flight_number
    )
    if probability is None:
        return {"available": False, "message": "Delay prediction unavailable for this flight."}
    return {"available": True, "probability_delay_over_2h": round(probability, 3)}


@mcp.tool()
def search_flights(
    origin: str, destination: str, departure_date: str, max_results: int = 5
) -> list[dict]:
    """Search bookable flights for a route and date (non-stop, one adult).

    Args:
        origin: Origin IATA airport code, e.g. "NCE".
        destination: Destination IATA airport code, e.g. "CDG".
        departure_date: ISO format "YYYY-MM-DD".
        max_results: Maximum number of offers to return (default 5).
    """
    options = _client().search_alternatives(
        origin, destination, date.fromisoformat(departure_date), max_results=max_results
    )
    return [
        {
            "flight": f"{o.carrier_code}{o.flight_number}",
            "route": f"{o.departure_iata}->{o.arrival_iata}",
            "departure": o.departure.isoformat(),
            "arrival": o.arrival.isoformat(),
            "price": f"{o.price_total:.2f} {o.currency}",
            "seats_available": o.seats_available,
        }
        for o in options
    ]


@mcp.tool()
def passenger_rights(question: str, top_k: int = 3) -> list[dict]:
    """Look up passenger rights and carrier disruption policies (EU261, rebooking,
    baggage, duty of care). Returns the most relevant policy passages with sources,
    so every entitlement you state can be cited.

    Args:
        question: Natural-language question, e.g. "compensation for a 3 hour delay".
        top_k: Number of passages to return (default 3).
    """
    passages = _retriever().retrieve(question, top_k=top_k)
    return [{"source": p.source, "text": p.text, "score": round(p.score, 2)} for p in passages]


@mcp.tool()
def handle_disruption(
    carrier_code: str, flight_number: str, departure_date: str, scenario: str = "delay"
) -> dict:
    """Run the full disruption-handling agent for a flight: status check, disruption
    assessment, rebooking search, policy retrieval and a grounded passenger message.

    Args:
        carrier_code: IATA carrier code, e.g. "AF".
        flight_number: Flight number, e.g. "1234".
        departure_date: ISO format "YYYY-MM-DD".
        scenario: In mock mode only: "delay", "cancellation" or "on_time".
    """
    result = run_agent(
        carrier_code, flight_number, date.fromisoformat(departure_date), scenario=scenario
    )
    event = result.get("event")
    recommendation = result.get("recommendation")
    return {
        "disruption": event.type.value if event else "unknown",
        "delay_minutes": event.delay_minutes if event else 0,
        "passenger_message": recommendation.summary if recommendation else None,
        "policy_sources": (
            [p.source for p in recommendation.policy_basis] if recommendation else []
        ),
        "trace": result.get("trace", []),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
