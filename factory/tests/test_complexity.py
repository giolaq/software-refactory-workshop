import sys
import unittest
from pathlib import Path


FACTORY_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FACTORY_DIR))

from complexity import function_complexities


class ComplexityBudgetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = function_complexities(FACTORY_DIR)

    def score(self, filename: str, function: str) -> int:
        matches = [
            item.score for item in self.results
            if item.path.name == filename and item.name == function
        ]
        self.assertTrue(matches, f"missing complexity score for {filename}:{function}")
        return max(matches)

    def test_production_functions_stay_within_global_budget(self):
        worst = self.results[0]
        self.assertLessEqual(
            worst.score, 75,
            f"{worst.path}:{worst.line} {worst.name} has score {worst.score}",
        )

    def test_public_dispatch_interfaces_remain_small(self):
        self.assertLessEqual(self.score("control_center.py", "build_commands"), 5)
        self.assertLessEqual(self.score("doctor.py", "run_doctor"), 2)
        self.assertLessEqual(self.score("orchestrator.py", "main"), 3)

    def test_primary_state_machines_keep_their_extracted_seams(self):
        self.assertLessEqual(self.score("control_center.py", "journey"), 60)
        self.assertLessEqual(self.score("orchestrator.py", "process"), 40)


if __name__ == "__main__":
    unittest.main()
