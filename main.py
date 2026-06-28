import schedule
import time
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from datetime import datetime
from db import init_db
from api import fetch_flights
from alerts import process_all_flights
from config import CHECK_INTERVAL_HOURS, ROUTE_IDA, ROUTE_VUELTA


def run_check():
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Chequeando vuelos...")
    try:
        ida_flights    = fetch_flights(ROUTE_IDA)
        vuelta_flights = fetch_flights(ROUTE_VUELTA)
        process_all_flights(ida_flights, vuelta_flights, ROUTE_IDA, ROUTE_VUELTA)
        print(f"[main] Listo. Proximo check en {CHECK_INTERVAL_HOURS}h.")
    except Exception as e:
        print(f"[main] Error: {e}")


if __name__ == "__main__":
    init_db()
    print(f"FlyBot arrancado - BUE->RIO | IDA <$250k | VUELTA <$150k | cada {CHECK_INTERVAL_HOURS}h")

    run_check()

    schedule.every(CHECK_INTERVAL_HOURS).hours.do(run_check)
    while True:
        schedule.run_pending()
        time.sleep(60)
