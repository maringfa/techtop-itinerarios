"""Reglas de exhibición; no accede a los archivos de origen."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


CR = ZoneInfo("America/Costa_Rica")
IMPORT_LIMIT = 20
IMPORT_HORIZON_DAYS = 30


def import_date(record):
    """ATP tiene prioridad; ETA solo se usa mientras ATP esté vacío."""
    return record["plant"] or record["eta"]


def build_board(imports, exports, demo=False, now=None):
    now = now or datetime.now(CR)
    today = now.date()
    window_end = today + timedelta(days=IMPORT_HORIZON_DAYS)
    arrivals = sorted(
        (x for x in imports if import_date(x) and today <= import_date(x) <= window_end
         and x["status"].strip().casefold() != "arrived"),
        key=lambda x: (import_date(x), x["container"]),
    )[:IMPORT_LIMIT]
    departures = sorted(
        (x for x in exports if x["departure"] and x["departure"] >= today and x["transfer"].strip()),
        key=lambda x: (x["departure"], x["transfer"]),
    )
    pending = [x for x in imports if not x["plant"] and x["status"].strip().casefold() != "arrived"]
    watch = sorted(
        (x for x in imports if x["status"].strip().casefold() != "arrived"
         and x["eta"] and 0 <= (x["eta"] - today).days <= 2),
        key=lambda x: x["eta"],
    )
    return {
        "demo": demo,
        "imports": [{"plant": x["plant"].isoformat() if x["plant"] else None,
                     "displayDate": import_date(x).isoformat(),
                     "dateType": "ATP" if x["plant"] else "ETA", "container": x["container"],
                     "hbl": x["hbl"], "items": x["items"]} for x in arrivals],
        "exports": [{"departure": x["departure"].isoformat(), "origin": x["origin"],
                     "reservation": x["reservation"], "container": x["container"],
                     "transfer": x["transfer"]} for x in departures],
        "port": {"eta": watch[0]["eta"].isoformat() if watch else None,
                 "watchCount": len(watch), "unscheduledCount": len(pending)},
        "today": today.isoformat(),
    }
