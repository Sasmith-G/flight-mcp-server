"""Tool-level tests (mock mode — offline and deterministic)."""

from amadeus_mcp_server.server import (
    flight_status,
    handle_disruption,
    passenger_rights,
    predict_delay,
    search_flights,
)


def test_flight_status_reports_delay():
    result = flight_status("AF", "1234", "2026-07-10")
    assert result["found"] is True
    assert result["flight"] == "AF1234"
    assert result["delay_minutes"] == 190
    assert result["cancelled"] is False


def test_predict_delay_returns_probability():
    result = predict_delay("NCE", "CDG", "2026-07-10T14:00", "AF", "1234")
    assert result["available"] is True
    assert 0 <= result["probability_delay_over_2h"] <= 1


def test_search_flights_returns_priced_offers():
    offers = search_flights("NCE", "CDG", "2026-07-10")
    assert len(offers) == 3
    assert all("EUR" in o["price"] for o in offers)
    assert offers[0]["route"] == "NCE->CDG"


def test_passenger_rights_cites_sources():
    passages = passenger_rights("compensation for a 3 hour delay")
    assert passages
    assert all(p["source"] and p["text"] for p in passages)
    assert any("eu261" in p["source"] for p in passages)


def test_handle_disruption_runs_full_pipeline():
    result = handle_disruption("AF", "1234", "2026-07-10", scenario="delay")
    assert result["disruption"] == "delay"
    assert result["delay_minutes"] == 190
    assert "AF6205" in result["passenger_message"]
    assert result["policy_sources"]
    assert len(result["trace"]) == 6


def test_handle_disruption_on_time_sends_nothing():
    result = handle_disruption("AF", "1234", "2026-07-10", scenario="on_time")
    assert result["disruption"] == "none"
    assert result["passenger_message"] is None
