"""Reglas de exhibición; no accede a los archivos de origen."""
from datetime import date, datetime
from zoneinfo import ZoneInfo


CR = ZoneInfo("America/Costa_Rica")


def build_board(imports, exports, demo=False, now=None):
    now = now or datetime.now(CR)
    today = now.date()
    arrivals = sorted(
        (x for x in imports if x["plant"] and x["plant"] >= today
         and x["status"].strip().casefold() != "arrived"),
        key=lambda x: (x["plant"], x["container"]),
    )
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
        "imports": [{"plant": x["plant"].isoformat(), "container": x["container"],
                     "hbl": x["hbl"], "items": x["items"]} for x in arrivals],
        "exports": [{"departure": x["departure"].isoformat(), "origin": x["origin"],
                     "reservation": x["reservation"], "container": x["container"],
                     "transfer": x["transfer"]} for x in departures],
        "port": {"eta": watch[0]["eta"].isoformat() if watch else None,
                 "watchCount": len(watch), "unscheduledCount": len(pending)},
        "today": today.isoformat(),
    }
