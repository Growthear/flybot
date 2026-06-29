from datetime import datetime
from db import download_db, upload_db, init_db
from api import fetch_flights
from alerts import process_all_flights
from config import ROUTE_IDA, ROUTE_VUELTA


def run_check():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Chequeando vuelos...")
    download_db()
    init_db()
    ida_flights    = fetch_flights(ROUTE_IDA)
    vuelta_flights = fetch_flights(ROUTE_VUELTA)
    process_all_flights(ida_flights, vuelta_flights, ROUTE_IDA, ROUTE_VUELTA)
    upload_db()
    print("Check completo.")


def lambda_handler(event, context):
    run_check()
    return {"statusCode": 200, "body": "ok"}


if __name__ == "__main__":
    import schedule
    import time

    run_check()
    schedule.every(2).hours.do(run_check)
    while True:
        schedule.run_pending()
        time.sleep(60)
