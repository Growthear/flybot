from datetime import datetime, timedelta
from config import (VOUCHER_ARS, STAY_DAYS_MIN, STAY_DAYS_MAX,
                    COMBO_THRESHOLD, IDA_STANDALONE_THRESHOLD,
                    VUELTA_STANDALONE_THRESHOLD, TOP_N_ALERTS)
from db import get_average_price, already_alerted_today, mark_alert_sent, save_price
from notifier import send_alert

LINK_IDA    = "https://flybondi.com/ar/search/dates?adults=1&children=0&currency=ARS&fromCityCode=BUE&infants=0&toCityCode=RIO&utm_origin=search_bar"
LINK_VUELTA = "https://flybondi.com/ar/search/dates?adults=1&children=0&currency=ARS&fromCityCode=RIO&infants=0&toCityCode=BUE&utm_origin=search_bar"


def _fmt_date(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        dias = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
        return f"{dias[dt.weekday()]} {dt.day:02d}/{dt.month:02d}"
    except Exception:
        return iso_str[:10]


def _fmt_price(p: float) -> str:
    return f"${p:,.0f}".replace(",", ".")


def _find_best_companion(flights: list[dict], anchor_date: str, anchor_is_ida: bool) -> dict | None:
    try:
        anchor = datetime.fromisoformat(anchor_date.replace("Z", "+00:00"))
    except Exception:
        return None

    min_d = anchor + timedelta(days=STAY_DAYS_MIN) if anchor_is_ida else anchor - timedelta(days=STAY_DAYS_MAX)
    max_d = anchor + timedelta(days=STAY_DAYS_MAX) if anchor_is_ida else anchor - timedelta(days=STAY_DAYS_MIN)

    candidates = [f for f in flights if f.get("lowestPrice") and _parse_date(f["departure"]) and min_d <= _parse_date(f["departure"]) <= max_d]
    if not candidates:
        candidates = [f for f in flights if f.get("lowestPrice")]
    return min(candidates, key=lambda x: x["lowestPrice"]) if candidates else None


def _parse_date(iso_str: str) -> datetime | None:
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _alert(key: str, msg: str, label: str) -> bool:
    if already_alerted_today(key):
        return False
    if send_alert(msg):
        mark_alert_sent(key)
        print(f"[alerts] {label}")
        return True
    return False


def _msg_combo(ida_flight: dict, vuelta_flight: dict) -> str:
    ida_p = ida_flight["lowestPrice"]
    vuelta_p = vuelta_flight["lowestPrice"]
    total = ida_p + vuelta_p
    bolsillo = max(0, total - VOUCHER_ARS)
    return (
        f"COMBO BUE-RIO | Ida + Vuelta bajo ${COMBO_THRESHOLD:,}\n\n"
        f"IDA:    {_fmt_date(ida_flight['departure'])}  -->  {_fmt_price(ida_p)} ARS\n"
        f"VUELTA: {_fmt_date(vuelta_flight['departure'])}  -->  {_fmt_price(vuelta_p)} ARS\n\n"
        f"TOTAL:   {_fmt_price(total)} ARS\n"
        f"Voucher: -{_fmt_price(VOUCHER_ARS)} ARS\n"
        f"Pagas:   {_fmt_price(bolsillo)} ARS de tu bolsillo\n\n"
        f"Ver IDA:    {LINK_IDA}\n"
        f"Ver vuelta: {LINK_VUELTA}"
    )


def _msg_ida_standalone(ida_flight: dict, best_vuelta: dict | None) -> str:
    ida_p = ida_flight["lowestPrice"]
    lines = [
        f"VUELO DE IDA MUY BARATO!\n",
        f"IDA: {_fmt_date(ida_flight['departure'])}  -->  {_fmt_price(ida_p)} ARS",
    ]
    if best_vuelta:
        vuelta_p = best_vuelta["lowestPrice"]
        total = ida_p + vuelta_p
        bolsillo = max(0, total - VOUCHER_ARS)
        lines.append(f"\nMejor vuelta disponible (~2 meses despues):")
        lines.append(f"VUELTA: {_fmt_date(best_vuelta['departure'])}  -->  {_fmt_price(vuelta_p)} ARS")
        lines.append(f"\nTOTAL:   {_fmt_price(total)} ARS")
        lines.append(f"Voucher: -{_fmt_price(VOUCHER_ARS)} ARS")
        lines.append(f"Pagas:   {_fmt_price(bolsillo)} ARS de tu bolsillo")
    lines.append(f"\nVer IDA: {LINK_IDA}")
    return "\n".join(lines)


def _msg_vuelta_standalone(vuelta_flight: dict, best_ida: dict | None) -> str:
    vuelta_p = vuelta_flight["lowestPrice"]
    lines = [
        f"VUELO DE VUELTA MUY BARATO!\n",
        f"VUELTA: {_fmt_date(vuelta_flight['departure'])}  -->  {_fmt_price(vuelta_p)} ARS",
    ]
    if best_ida:
        ida_p = best_ida["lowestPrice"]
        total = ida_p + vuelta_p
        bolsillo = max(0, total - VOUCHER_ARS)
        lines.append(f"\nMejor ida disponible (~2 meses antes):")
        lines.append(f"IDA: {_fmt_date(best_ida['departure'])}  -->  {_fmt_price(ida_p)} ARS")
        lines.append(f"\nTOTAL:   {_fmt_price(total)} ARS")
        lines.append(f"Voucher: -{_fmt_price(VOUCHER_ARS)} ARS")
        lines.append(f"Pagas:   {_fmt_price(bolsillo)} ARS de tu bolsillo")
    lines.append(f"\nVer vuelta: {LINK_VUELTA}")
    return "\n".join(lines)


def process_all_flights(ida_flights: list[dict], vuelta_flights: list[dict], *_):
    # Guardar historial de precios
    for f in ida_flights:
        if f.get("departure") and f.get("lowestPrice"):
            save_price(f"IDA:{f['departure']}", f["lowestPrice"])
    for f in vuelta_flights:
        if f.get("departure") and f.get("lowestPrice"):
            save_price(f"VUELTA:{f['departure']}", f["lowestPrice"])

    # --- 1. COMBO: IDA + VUELTA compatible bajo $400k ---
    combos = []
    for ida in ida_flights:
        if not ida.get("lowestPrice"):
            continue
        companion = _find_best_companion(vuelta_flights, ida["departure"], anchor_is_ida=True)
        if companion and ida["lowestPrice"] + companion["lowestPrice"] < COMBO_THRESHOLD:
            combos.append((ida["lowestPrice"] + companion["lowestPrice"], ida, companion))

    combos.sort(key=lambda x: x[0])
    sent_combo = 0
    for total, ida, vuelta in combos:
        if sent_combo >= TOP_N_ALERTS:
            break
        key = f"COMBO:IDA:{ida['departure'][:10]}:VUELTA:{vuelta['departure'][:10]}"
        if _alert(key, _msg_combo(ida, vuelta), f"COMBO {ida['departure'][:10]} + {vuelta['departure'][:10]} -> {_fmt_price(total)}"):
            sent_combo += 1

    # --- 2. IDA SUELTA: BUE->RIO bajo $240k ---
    qualifying_ida = sorted(
        [f for f in ida_flights if f.get("lowestPrice") and f["lowestPrice"] < IDA_STANDALONE_THRESHOLD],
        key=lambda x: x["lowestPrice"]
    )
    sent_ida = 0
    for flight in qualifying_ida:
        if sent_ida >= TOP_N_ALERTS:
            break
        key = f"IDA_CHEAP:{flight['departure'][:10]}"
        companion = _find_best_companion(vuelta_flights, flight["departure"], anchor_is_ida=True)
        if _alert(key, _msg_ida_standalone(flight, companion), f"IDA SUELTA {flight['departure'][:10]} -> {_fmt_price(flight['lowestPrice'])}"):
            sent_ida += 1

    # --- 3. VUELTA SUELTA: RIO->BUE bajo $120k ---
    qualifying_vuelta = sorted(
        [f for f in vuelta_flights if f.get("lowestPrice") and f["lowestPrice"] < VUELTA_STANDALONE_THRESHOLD],
        key=lambda x: x["lowestPrice"]
    )
    sent_vuelta = 0
    for flight in qualifying_vuelta:
        if sent_vuelta >= TOP_N_ALERTS:
            break
        key = f"VUELTA_CHEAP:{flight['departure'][:10]}"
        companion = _find_best_companion(ida_flights, flight["departure"], anchor_is_ida=False)
        if _alert(key, _msg_vuelta_standalone(flight, companion), f"VUELTA SUELTA {flight['departure'][:10]} -> {_fmt_price(flight['lowestPrice'])}"):
            sent_vuelta += 1

    # Si no hubo ninguna alerta, manda heartbeat en cada run
    if sent_combo + sent_ida + sent_vuelta == 0:
        now = datetime.now().strftime("%d/%m %H:%M")
        send_alert(f"No se encontraron vuelos baratos en este check ({now}).\nEl bot esta funcionando correctamente.")
        print("[alerts] heartbeat enviado")
