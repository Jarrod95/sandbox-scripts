# Fitness & Health

Personal fitness analytics: MyFitnessPal intake and weight, Withings activity and health metrics, body composition, forecasts and reporting.

| Location | Contents |
| --- | --- |
| [MyFitnessPal](myfitnesspal/) | Browser exporters, all MFP data, analysis notebook and [journey report](myfitnesspal/WEIGHT_JOURNEY.md) |
| [Withings](withings/) | API extraction notebook and Withings data directory |
| [fitness_analysis.py](fitness_analysis.py) | Shared calculations and scenario functions |
| [ROADMAP.md](ROADMAP.md) | Prioritized, bot-readable development plan |

Install root dependencies with `pip install -r requirements.txt`, set `CLIENT_ID` and `CLIENT_SECRET` in an **untracked** root `.env`, then open the notebooks. Their imports resolve `fitness_health/fitness_analysis.py` and their inputs stay under this folder.

**Boundary:** no fitness CSV, JSON, XLSX, databases, notebook outputs or generated reports should be written to repository root. Browser exporters require explicit folder selection. Protect private health data before pushing to GitHub.
