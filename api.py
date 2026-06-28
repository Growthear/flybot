import os
from curl_cffi import requests as cf_requests
from config import FLYBONDI_URL, FLYBONDI_AUTH, CURRENCY

PROXY = os.environ.get("PROXY_URL")  # None cuando corre local sin proxy

GRAPHQL_QUERY = """
query DatesContainerQuery(
  $origin: String!
  $destination: String!
  $currency: String!
  $start: Timestamp!
  $end: Timestamp!
) {
  departures: fares(origin: $origin, destination: $destination, currency: $currency, start: $start, end: $end, sort: "departure") {
    id
    departure
    fares {
      price
      fCCode
      fBCode
      roundtrip
    }
    lowestPrice
    earliestDepartureTime
    flightsPerDay
  }
}
"""


def fetch_flights(route: dict) -> list[dict]:
    payload = {
        "operationName": "DatesContainerQuery",
        "variables": {
            "origin": route["origin"],
            "destination": route["destination"],
            "currency": CURRENCY,
            "start": route["start_ms"],
            "end": route["end_ms"],
        },
        "query": GRAPHQL_QUERY,
    }

    headers = {
        "authorization": FLYBONDI_AUTH,
        "content-type": "application/json",
        "accept": "application/json",
        "accept-language": "es-AR,es-419;q=0.9,es;q=0.8",
        "origin": "https://flybondi.com",
        "referer": route["referer"],
        "x-fo-flow": "ibe",
        "x-fo-market-origin": "ar",
        "x-fo-shopping-id": "",
        "x-fo-ui-version": "2.230.0",
    }

    # curl_cffi imita el fingerprint TLS de Chrome — pasa Cloudflare sin browser real
    kwargs = dict(json=payload, headers=headers, impersonate="chrome131", timeout=30)
    if PROXY:
        kwargs["proxies"] = {"https": PROXY, "http": PROXY}

    response = cf_requests.post(FLYBONDI_URL, **kwargs)

    if not response.ok:
        raise RuntimeError(f"API respondio {response.status_code}: {response.text[:300]}")

    data = response.json()

    if not isinstance(data, dict):
        raise RuntimeError(f"Respuesta inesperada: {str(data)[:200]}")

    departures = data.get("data", {}).get("departures", [])
    print(f"[api] {route['label']}: {len(departures)} fechas recibidas")
    return departures
