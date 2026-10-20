# sandbox-scripts

Browser-console scripts for exporting your own MyFitnessPal food diary and weight history. No installation or API key required.

## Quick start

1. Sign in to [MyFitnessPal](https://www.myfitnesspal.com/) in a desktop browser.
2. Open the relevant page: **Food Diary** for food entries, or **Reports → Progress / Weight** for weight history.
3. Open Developer Tools (**F12** or **Ctrl+Shift+J** on Windows; **Cmd+Option+J** on macOS) and select **Console**.
4. Open the script below, copy its **entire contents**, paste into the Console and press **Enter**. If your browser blocks pasting, follow its on-screen instructions.
5. Wait for the completion message. Find the downloaded files in your Downloads folder; allow multiple downloads if prompted.

| Script | Outputs |
| --- | --- |
| [`mfp-fooddiary.js`](./mfp-fooddiary.js) | `mfp_2026_apr_oct_foods.csv`, `mfp_2026_apr_oct_meals.csv`, `mfp_2026_apr_oct_daily.csv`, `mfp_2026_apr_oct_full.json` |
| [`mfp-weight-history.js`](./mfp-weight-history.js) | `myfitnesspal_weight_history.csv` |

## Change the date range

Both scripts default to **1 April–20 October 2026**, inclusive. Edit the `CONFIG` object near the top before copying:

- **Food diary:** `start`, `end` (format `YYYY-MM-DD`), and optionally `prefix`.
- **Weight history:** `startDate`, `endDate` (same format). `periods: [365, 180, 90, 30]` specifies API lookback windows, **not** the output date filter.

**Weight-specific caveats:** Dates returned without a year are assumed to be **2026** in `parseDate` (`match[3] || 2026`); update this if exporting another year. The script assumes the weight chart reports **kilograms**. Verify units before using `weight_kg`.

## Verify your results

- **Food diary:** inspect the Console summary for `errors` and `calorie_mismatches`; the daily CSV includes `validated` and `calorie_difference`. Missing food logs do **not** mean zero calories consumed. To stop the crawl, enter `window.mfpStop = true`.
- **Weight history:** inspect the Console's `REQUEST RESULTS` table, the number of unique measurements and first/last dates. The reports API may return sampled **chart points**, not every recorded weigh-in; the 365-day window is not guaranteed to work.

## Troubleshooting

- **No results / login redirect:** confirm you're signed in and on the correct MyFitnessPal page, then refresh and retry.
- **Food diary parsing error:** the script depends on MyFitnessPal's `#diary-table` HTML; website changes can break it. Review the Console errors.
- **Incomplete weight history:** review each API period's status. The script queries `/api/services/reports/results/progress/1/{days}` and can export only the points returned.
- **Downloads blocked:** allow multiple downloads for MyFitnessPal.
- **HTTP 429 / rate limit:** stop and retry later; do not raise concurrency to bypass rate limits.

The scripts run in your logged-in browser using your existing MyFitnessPal session. They are unofficial and may require updates as the website changes. **Never share cookies or authentication tokens.** Exports contain personal health data; keep them private.
