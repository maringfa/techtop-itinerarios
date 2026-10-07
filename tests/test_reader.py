from datetime import datetime, time, timedelta
from pathlib import Path
import sys
import unittest
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from domain import build_board
from reader import read_xlsx


ROOT = Path(__file__).resolve().parents[1]


class ItineraryTests(unittest.TestCase):
    def test_eta_is_used_only_when_atp_is_missing(self):
        now = datetime(2026, 10, 7, 12, tzinfo=ZoneInfo("America/Costa_Rica"))
        today = now.date()
        def imp(container, plant, eta, status="In transit"):
            return {"container": container, "plant": plant, "eta": eta, "status": status,
                    "hbl": "HBL-EJEMPLO", "items": "Plywood"}
        tomorrow = today + timedelta(days=1)
        imports = [imp("ATP-futuro", tomorrow, today),
                   imp("ETA-hoy", None, today),
                   imp("ATP-hoy", today, tomorrow),
                   imp("ATP-pasado", today - timedelta(days=1), tomorrow),
                   imp("ETA-pasado", None, today - timedelta(days=1)),
                   imp("Ya-arribo", None, tomorrow, "Arrived"),
                   imp("Sin-fechas", None, None)]
        board = build_board(imports, [], now=now)
        self.assertEqual([x["container"] for x in board["imports"]],
                         ["ATP-hoy", "ETA-hoy", "ATP-futuro"])
        self.assertEqual([x["displayDate"] for x in board["imports"]],
                         [today.isoformat(), today.isoformat(), tomorrow.isoformat()])
        fallback = next(x for x in board["imports"] if x["container"] == "ETA-hoy")
        self.assertEqual(fallback["dateType"], "ETA")
        self.assertIsNone(fallback["plant"])
        imports[1]["plant"] = tomorrow
        updated = next(x for x in build_board(imports, [], now=now)["imports"]
                       if x["container"] == "ETA-hoy")
        self.assertEqual(updated["dateType"], "ATP")
        self.assertEqual(updated["displayDate"], tomorrow.isoformat())
        self.assertNotIn("eta", updated)

    def test_upcoming_movements_exclude_past_and_arrived_and_sort_by_date(self):
        now = datetime(2026, 10, 7, 12, tzinfo=ZoneInfo("America/Costa_Rica"))
        today = now.date()
        def imp(days, status="In transit"):
            return {"plant": today + timedelta(days=days), "status": status,
                    "container": str(days), "hbl": "example", "items": "Plywood", "eta": today}
        def exp(days, transfer="example"):
            return {"departure": today + timedelta(days=days), "transfer": transfer,
                    "origin": "Atlanta", "container": "example", "reservation": "example"}
        board = build_board([imp(2), imp(-1), imp(1, "Arrived"), imp(0)],
                            [exp(2), exp(-1), exp(0), exp(1, "")], now=now)
        dates = [today.isoformat(), (today + timedelta(days=2)).isoformat()]
        self.assertEqual([x["plant"] for x in board["imports"]], dates)
        self.assertEqual([x["departure"] for x in board["exports"]], dates)

    def test_merged_shared_dates_and_individual_arrivals(self):
        rows = read_xlsx(ROOT / "samples/importaciones_ficticias.xlsx", "import", "Importaciones", 1)
        self.assertEqual(rows[1]["hbl"], rows[6]["hbl"])
        self.assertEqual(rows[1]["eta"], rows[6]["eta"])
        self.assertEqual(len({x["container"] for x in rows}), len(rows))
        self.assertTrue(any(x["plant"] is None for x in rows))

    def test_filters_and_overflow_data_are_not_lost(self):
        imports = read_xlsx(ROOT / "samples/importaciones_ficticias.xlsx", "import", "Importaciones", 1)
        exports = read_xlsx(ROOT / "samples/exportaciones_ficticias.xlsx", "export", "Exportaciones", 1)
        sample_today = imports[0]["plant"]
        board = build_board(imports, exports, demo=True,
                            now=datetime.combine(sample_today, time(12), ZoneInfo("America/Costa_Rica")))
        self.assertEqual(len(board["imports"]), 14)
        self.assertEqual(len(board["exports"]), 2)
        self.assertEqual(board["port"]["unscheduledCount"], 1)
        self.assertEqual(sum(x["plant"] == (sample_today + timedelta(days=1)).isoformat()
                             for x in board["imports"]), 12)
        fallback = next(x for x in board["imports"] if x["plant"] is None)
        self.assertEqual(fallback["dateType"], "ETA")
        self.assertEqual(fallback["displayDate"], (sample_today + timedelta(days=1)).isoformat())


if __name__ == "__main__":
    unittest.main()
