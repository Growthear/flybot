import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_IDS = [int(x) for x in os.environ["TELEGRAM_CHAT_IDS"].split(",")]
FLYBONDI_AUTH = os.environ["FLYBONDI_AUTH"]
VOUCHER_ARS = int(os.environ.get("VOUCHER_ARS", 241_000))

CURRENCY = "ARS"

ROUTE_IDA = {
    "origin": "BUE",
    "destination": "RIO",
    "label": "BUE->RIO",
    "start_ms": 1782820800000,
    "end_ms":   1793448000000,
    "referer": "https://flybondi.com/ar/search/dates?adults=1&children=0&currency=ARS&fromCityCode=BUE&infants=0&toCityCode=RIO&utm_origin=search_bar",
}

ROUTE_VUELTA = {
    "origin": "RIO",
    "destination": "BUE",
    "label": "RIO->BUE",
    "start_ms": 1788177600000,
    "end_ms":   1798718400000,
    "referer": "https://flybondi.com/ar/search/dates?adults=1&children=0&currency=ARS&fromCityCode=RIO&infants=0&toCityCode=BUE&utm_origin=search_bar",
}

ROUTES = [ROUTE_IDA, ROUTE_VUELTA]

COMBO_THRESHOLD             = 400_000
IDA_STANDALONE_THRESHOLD    = 240_000
VUELTA_STANDALONE_THRESHOLD = 120_000

DISCOUNT_FACTOR = 0.80
STAY_DAYS_MIN   = 45
STAY_DAYS_MAX   = 75
TOP_N_ALERTS    = 5
CHECK_INTERVAL_HOURS = 6

FLYBONDI_URL = "https://flybondi.com/graphql"
