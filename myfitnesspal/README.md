# MyFitnessPal exports and projections

Run [mfp-fooddiary.js](mfp-fooddiary.js) while signed in to the browser food diary, and [mfp-weight-history.js](mfp-weight-history.js) from the weight/progress page. Configure the dates at the top of each script; the `*_daily.csv`, `*_foods.csv`, `*_meals.csv`, `*_full.json` and `*weight*.csv` exports are saved directly into [data/](data/) after you approve access through the folder picker. **Choose** `C:\\Users\\jarro\\OneDrive\\Documents\\Codebases\\sandbox-scripts\\myfitnesspal\\data` when prompted. The scripts overwrite same-named exports on rerun. If your browser does not support the File System Access API, files instead download through the browser's normal Downloads destination.

Open [weight_journey.ipynb](weight_journey.ipynb) for diagnostic tables, calorie/adherence charts, weight history, optional Withings comparison and scenario projections. The notebook detects files in `data/` automatically and draws figures without requiring Withings credentials.

Read [WEIGHT_JOURNEY.md](WEIGHT_JOURNEY.md) for a shareable, plain-language overview of the cut, maintenance until April 2027 and potential long-term 95 kg at 8% or 10% scenarios.

**Data limitations:** Zero food entries means *untracked*, not fasting. Low-calorie days may be incomplete, and the weight export may carry forward chart values between actual weigh-ins. These unofficial browser scripts depend on the current site structure. Keep personal data private.

**Browser security:** JavaScript running on MyFitnessPal cannot silently select a full Windows path. Each run displays an on-page button; click it to grant the browser read/write access to the local folder before extraction starts. Use a recent Chromium-based browser over HTTPS. The scripts do not send exported data to another server.
