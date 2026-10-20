# Fitness & Health

Locally hosted analysis of MyFitnessPal food and weight exports, optional Withings activity, energy-balance scenarios and reports. Uses the shared [analytics functions](fitness_analysis.py); no Streamlit or cloud deployment.

## Run locally (Windows PowerShell, from repository root)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m fitness_health.local_app
```

For lifting progress, download the Gym Day ZIP export and copy it **without unzipping** into `fitness_health/gymday/data/` (see [Gym Day instructions](gymday/README.md)). Use the **Strength training** tab with its exercise dropdown; the dashboard now defaults to a light theme.

Open **http://127.0.0.1:8765**. Stop with `Ctrl+C`. Optional: `python -m fitness_health.local_app --port 8766`.

The dashboard reads CSVs from `fitness_health/myfitnesspal/data/` and optionally `fitness_health/withings/data/withings_daily_activity.csv`. Nothing is uploaded; the server binds to loopback only. A missing MFP export is shown as an error rather than fabricated data.

Generate a local weekly Markdown summary:

```powershell
python -m fitness_health.weekly_report
python -m fitness_health.weekly_report --end 2026-10-20 --output fitness_health/reports/week.md
python -m unittest discover -s fitness_health/tests -v
```

Exports: [MFP instructions](myfitnesspal/README.md), [Withings instructions](withings/README.md). Existing `weight_journey.ipynb` remains supported. See [ROADMAP](ROADMAP.md) for version history, next priorities and limitations.

**Privacy:** `fitness_health/myfitnesspal/data/`, `fitness_health/withings/data/`, `fitness_health/gymday/data/` and generated reports must not be committed. Previously tracked health exports remain in the public repository and Git history until separately remediated. Review repository history and visibility.
