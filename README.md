# Fitness data sandbox

Reproducible personal fitness-data extraction, analysis and weight-planning notebooks.

| Folder | Contents |
| --- | --- |
| [withings](withings/) | Withings API notebook: OAuth, activity, workouts, sleep, body measures, heart data, exports and plots |
| [myfitnesspal](myfitnesspal/) | Browser exporters, source CSV/JSON data, weight forecasts and [shareable journey report](myfitnesspal/WEIGHT_JOURNEY.md) |
| [fitness_analysis.py](fitness_analysis.py) | Shared, conservative data cleaning and energy-balance forecast functions |

## Start

```bash
python -m pip install -r requirements.txt
cp .env.example .env  # populate CLIENT_ID and CLIENT_SECRET locally
jupyter lab
```

Open `withings/withings-mfp-calories.ipynb` or `myfitnesspal/weight_journey.ipynb`. The notebook finds the repository root automatically, so it works from either directory.

Never commit `.env`, access tokens, authorization codes or raw credentials. CSV, JSON and XLSX are intentionally allowed by `.gitignore`; the personal exports already committed here may contain sensitive health data, so assess repository visibility before sharing.

**Interpretation:** Withings expenditure is an estimate, missing MyFitnessPal days are untracked rather than zero-intake, and repeated scale values in the exported weight history may be chart carry-forwards.
