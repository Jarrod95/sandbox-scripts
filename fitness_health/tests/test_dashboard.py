"""Self-contained, synthetic tests; no personal data or credentials needed."""
import json
import unittest
import pandas as pd

from fitness_health.fitness_analysis import join_data, forecast, lean_goal_table
from fitness_health.quality import audit_frame
from fitness_health.weekly_report import render_report
from fitness_health.local_app import make_handler, HTML


class TestFitness(unittest.TestCase):
    def setUp(self):
        self.daily = pd.DataFrame({
            "date": pd.to_datetime(["2026-10-01", "2026-10-02", "2026-10-03"]),
            "calories": [1800., float("nan"), 500.],
            "protein_g": [150., float("nan"), 30.],
            "carbs_g": [130., float("nan"), 20.],
            "fat_g": [50., float("nan"), 10.],
            "food_entries": [3, 0, 1],
            "logged": [True, False, True],
            "plausibly_complete": [True, False, False],
        })
        self.weights = pd.DataFrame({
            "date": self.daily.date, "weight_kg": [87., 87., 86.5],
            "changed_from_previous": [True, False, True],
        })
        self.activity = pd.DataFrame({
            "date": self.daily.date, "tdee_calories": [2500., 2400., 2600.],
            "active_burned_calories": [400., 300., 500.],
            "steps": [9000, 8000, 10000],
        })
        self.frame = join_data(self.daily, self.weights, self.activity)

    def test_missing_food_is_not_zero(self):
        self.assertTrue(pd.isna(self.frame.loc[1, "calories"]))
        self.assertTrue(pd.isna(self.frame.loc[1, "observed_deficit_kcal"]))

    def test_partial_food_excluded_from_deficit(self):
        self.assertTrue(pd.isna(self.frame.loc[2, "observed_deficit_kcal"]))
        self.assertEqual(self.frame.loc[0, "observed_deficit_kcal"], 700.)

    def test_withings_total_is_not_double_counted(self):
        self.assertEqual(self.frame.loc[0, "tdee_calories"], 2500.)

    def test_audit_completeness(self):
        result = audit_frame(self.frame)
        self.assertEqual(result["unknown_intake_days"], 1)
        self.assertEqual(result["possibly_partial_days"], 1)
        self.assertEqual(result["plausibly_complete_days"], 1)

    def test_duplicate_dates_rejected(self):
        bad = pd.concat([self.frame, self.frame.tail(1)])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit_frame(bad)

    def test_invalid_weight_rejected(self):
        bad = self.frame.copy()
        bad.loc[0, "weight_kg"] = -1
        with self.assertRaisesRegex(ValueError, "Invalid"):
            audit_frame(bad)

    def test_forecast_scenarios(self):
        path, milestones = forecast(start_weight=87, days=30)
        self.assertFalse(path.empty)
        self.assertEqual(path.iloc[0].weight_kg, 87)
        self.assertEqual(len(milestones), 5)

    def test_ffmi(self):
        goals = lean_goal_table(height_m=1.77)
        self.assertAlmostEqual(goals.iloc[0].ffmi, 85.5 / 1.77**2)

    def test_weekly_report_does_not_invent_intake(self):
        report = render_report(self.frame)
        self.assertIn("Missing/unknown intake: 1", report)
        self.assertIn("Plausibly complete diary: 1", report)

    def test_local_html_has_no_remote_assets(self):
        self.assertIn("127.0.0.1 only", HTML)
        self.assertNotIn("https://", HTML)


if __name__ == "__main__":
    unittest.main()
