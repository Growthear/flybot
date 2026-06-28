import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from db import init_db
from api import fetch_flights
from alerts import process_all_flights
from config import ROUTE_IDA, ROUTE_VUELTA

init_db()
ida_flights    = fetch_flights(ROUTE_IDA)
vuelta_flights = fetch_flights(ROUTE_VUELTA)
process_all_flights(ida_flights, vuelta_flights, ROUTE_IDA, ROUTE_VUELTA)
print("CHECK COMPLETO")
