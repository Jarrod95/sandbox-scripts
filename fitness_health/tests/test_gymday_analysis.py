"""Synthetic Gym Day importer tests; no personal exports in Git."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from fitness_health.gymday_analysis import load_training


class GymDayTests(unittest.TestCase):
    def test_missing_export(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(load_training(Path(directory))["available"])

    def test_training_aggregation(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "gymday" / "data"
            folder.mkdir(parents=True)
            sessions = [{
                "startDate": 1760000000000,
                "workoutSessionExercises": [{
                    "exercise": {"id": "bench-id", "name": "Bench Press"},
                    "workoutSessionSets": [
                        {"weight": 100, "reps": 5, "measurementUnit": "kg", "isComplete": True},
                        {"weight": 60, "reps": 10, "warmUp": True},
                        {"weight": 220, "reps": 5, "measurementUnit": "lb", "isComplete": True},
                        {"weight": 110, "reps": 5, "isComplete": False}
                    ]
                }]
            }]
            with zipfile.ZipFile(folder / "example.zip", "w") as archive:
                archive.writestr("WorkoutSession.json", json.dumps(sessions))
            data = load_training(Path(directory))
            self.assertEqual(data["summary"]["sets"], 2)
            self.assertEqual(data["summary"]["workouts"], 1)
            self.assertEqual(data["exercises"][0]["sessions"], 1)
            self.assertAlmostEqual(data["exercises"][0]["history"][0]["volume_kg"], 100*5 + 220*.45359237*5, places=1)


if __name__ == "__main__":
    unittest.main()
