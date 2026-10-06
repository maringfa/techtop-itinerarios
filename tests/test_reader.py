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
        self.assertEqual(len(board["imports"]), 13)
        self.assertEqual(len(board["exports"]), 2)
        self.assertEqual(board["port"]["unscheduledCount"], 1)
        self.assertEqual(sum(x["plant"] == (sample_today + timedelta(days=1)).isoformat()
                             for x in board["imports"]), 12)


if __name__ == "__main__":
    unittest.main()
