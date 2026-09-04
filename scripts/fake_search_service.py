"""A stand-in for the trip search service, so the plugin can be driven with no account.

It speaks the two shapes `cora.plugins.travel.trips` reads — Google Flights and Google
Hotels as SerpApi returns them — and makes its prices out of the dates it was asked
about, so a window really does have a cheapest week in it. Nothing here is real: it is
somewhere to point a demonstration.

    uv run python scripts/fake_search_service.py
    export CORA_PLUGIN_TRAVEL_SERPAPI_KEY=anything
    export CORA_PLUGIN_TRAVEL_SEARCH_URL=http://127.0.0.1:8909/search
"""

import argparse
import datetime
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

PORT = 8909
CARRIERS = ("TAP Air Portugal", "Lufthansa", "Ryanair", "Iberia")
HOTELS = (
    ("Alfama Rooms", 3),
    ("Baixa Suites", 4),
    ("Chiado Residence", 5),
    ("Graca Hostel", 1),
)


def _price(seed: str, low: int, spread: int) -> int:
    """A price that is always the same for the same day, and different for the next
    one — which is what makes a window worth searching."""
    return low + sum(ord(letter) * 7 for letter in seed) % spread


def _flights(asked: dict[str, str]) -> dict[str, Any]:
    out = asked.get("outbound_date", "2026-01-01")
    back = asked.get("return_date", out)
    ceiling = int(asked.get("max_price", 0)) or None
    legs = 1 if asked.get("stops") == "1" else 2
    offers = []
    for index, carrier in enumerate(CARRIERS):
        fare = _price(f"{out}{carrier}", 140, 420)
        if ceiling and fare > ceiling:
            continue
        offers.append(
            {
                "flights": [
                    {
                        "airline": carrier,
                        "flight_number": f"{carrier[:2].upper()} 1{index}0",
                    }
                ]
                * (1 if index % 2 else legs),
                "price": fare,
                "departure_date": out,
                "return_date": back,
            }
        )
    return {"best_flights": offers[:2], "other_flights": offers[2:]}


def _nights(asked: dict[str, str]) -> int:
    try:
        first = datetime.date.fromisoformat(asked["check_in"])
        last = datetime.date.fromisoformat(asked["check_out"])
    except (KeyError, ValueError):
        return 7
    return max(1, (last - first).days)


def _hotels(asked: dict[str, str]) -> dict[str, Any]:
    stay = _nights(asked)
    ceiling = int(asked.get("max_price", 0)) or None
    allowed = {int(star) for star in asked.get("hotel_class", "1,2,3,4,5").split(",")}
    found = []
    for name, stars in HOTELS:
        if stars not in allowed:
            continue
        total = _price(f"{asked.get('check_in', '')}{name}", 45, 160) * stay
        if ceiling and total > ceiling:
            continue
        found.append(
            {
                "name": name,
                "hotel_class": f"{stars}-star hotel",
                "overall_rating": 3.5 + stars / 10,
                "total_rate": {"lowest": f"€{total}", "extracted_lowest": total},
            }
        )
    return {"properties": found}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        asked = {
            name: values[0]
            for name, values in parse_qs(urlparse(self.path).query).items()
        }
        engine = asked.get("engine", "")
        shown = ", ".join(f"{k}={v}" for k, v in asked.items() if k != "api_key")
        print(f"  {engine}: {shown}")
        if engine == "google_hotels":
            body = _hotels(asked)
        elif engine == "google_flights":
            body = _flights(asked)
        else:
            body = {"error": f"no engine called {engine!r}"}
        written = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(written)))
        self.end_headers()
        self.wfile.write(written)

    def log_message(self, format: str, *args: Any) -> None:
        """Quiet: the line printed above says more than the access log would."""


def main() -> None:
    parsed = argparse.ArgumentParser(description=__doc__)
    parsed.add_argument("--port", type=int, default=PORT)
    port = parsed.parse_args().port
    print(f"invented prices on http://127.0.0.1:{port}/search — ctrl-c to stop")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
