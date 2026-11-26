import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = PROJECT_ROOT / "demo/test_cases"


class DemoCaseTests(unittest.TestCase):
    def test_manifest_and_videos_are_complete(self):
        rows = json.loads(
            (CASE_ROOT / "cases.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows), 5)
        self.assertEqual(len({row["id"] for row in rows}), 5)
        self.assertEqual(
            sum(bool(row.get("reference_known")) for row in rows), 4)
        for row in rows:
            video = CASE_ROOT / row["path"]
            self.assertTrue(video.exists(), video)
            self.assertGreater(video.stat().st_size, 50_000)
            self.assertLess(video.stat().st_size, 1_000_000)


if __name__ == "__main__":
    unittest.main()
