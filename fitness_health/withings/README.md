# Withings data extraction

Open [withings-mfp-calories.ipynb](withings-mfp-calories.ipynb) from JupyterLab. Install root `requirements.txt` first and place `CLIENT_ID` and `CLIENT_SECRET` in an untracked root `.env`.

The notebook groups OAuth, daily activity, workout sessions, body measures, sleep summaries, sleep epochs and heart events. Each section prints a data table and visualisation where records are available. It exports normalized CSVs to `withings/data/`, plus a combined CSV for the MyFitnessPal analysis.

Not every account or device provides every metric. Individual API sections fail independently with a visible warning; missing metrics are never imputed as zero. OAuth callback URLs and tokens must not be saved in notebook cells or committed outputs.

Use [MyFitnessPal analysis](../myfitnesspal/weight_journey.ipynb) for calorie-intake and weight-loss projections.
