import unittest
from bench.metrics import evaluate, latency, paired_comparison, wilson


def row(case_id, expected, actual, attempt=True):
    return {"id": case_id, "expected_route": expected, "actual_route": actual,
            "message": "synthetic fixture", "context": {}, "rationale": "fixture only", "tags": ["fixture"],
            "decision_wall_ms": 12 if attempt else None,
            "attempts": [{"actual_route": actual, "wall_ms": 10, "error_kind": "schema" if actual is None else None,
                "accounted_usd": 0.01, "usage": None}] if attempt else []}


class MetricTests(unittest.TestCase):
    def test_errors_stay_in_denominator_and_wrong_automation(self):
        rows = [row("1", "status", "status"), row("2", "operator", "answer"),
                row("3", "answer", "operator"), row("4", "answer", None), row("5", "status", None, False)]
        m = evaluate(rows)
        self.assertEqual((m["correct"], m["n_tasks"]), (1, 5))
        self.assertEqual(m["accuracy"], .2)
        self.assertEqual(m["confusion_matrix"]["answer"]["error"], 1)
        self.assertEqual(m["confusion_matrix"]["status"]["not_run"], 1)
        self.assertEqual(m["unsafe_automation_count"], 1)
        self.assertEqual(m["wrong_automation_fraction_of_automated"], .5)
        self.assertEqual(m["operator_fraction"], .2)
        self.assertEqual(m["not_run_count"], 1)
        self.assertAlmostEqual(m["macro_f1"], (2/3)/3)
        self.assertAlmostEqual(m["cost_upper_accounted_usd"], .04)
        self.assertFalse(m["cost_complete"])

    def test_all_operator_is_not_accurate(self):
        m = evaluate([row("1", "status", "operator"), row("2", "answer", "operator"), row("3", "operator", "operator")])
        self.assertEqual(m["accuracy"], 1/3)
        self.assertEqual(m["operator_fraction"], 1)
        self.assertEqual(m["automation_fraction"], 0)
        self.assertIsNone(m["wrong_automation_fraction_of_automated"])

    def test_latency_nearest_rank_and_wilson(self):
        self.assertEqual(latency(list(range(1, 101)))["p95_ms"], 95)
        self.assertEqual(latency(list(range(1, 101)))["median_ms"], 50.5)
        self.assertIsNone(latency([])["p95_ms"])
        self.assertAlmostEqual(wilson(50, 100)[0], .4038, places=3)

    def test_exact_paired_disagreement(self):
        left = [row(str(i), "answer", "answer") for i in range(6)]
        right = [row(str(i), "answer", "operator") for i in range(6)]
        p = paired_comparison(left, right)
        self.assertEqual(len(p["disagreements"]), 6)
        self.assertEqual(p["jev_only_correct"], 6)
        self.assertAlmostEqual(p["mcnemar_exact_two_sided_p"], .03125)
