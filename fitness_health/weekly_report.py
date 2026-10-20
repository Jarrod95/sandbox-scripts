"""On-demand, local Markdown weekly report. No secrets or data leave your machine."""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

from fitness_health.fitness_analysis import load_mfp, load_withings, join_data
from fitness_health.quality import audit_frame

ROOT = Path(__file__).resolve().parent


def render_report(frame, end=None):
    end_date = pd.Timestamp(end).normalize() if end else frame.date.max()
    recent = frame.loc[frame.date.between(end_date - pd.Timedelta(days=6), end_date)].copy()
    if recent.empty:
        raise ValueError("No observations for this week")
    quality = audit_frame(recent)
    full = recent.loc[recent.plausibly_complete]
    observed = recent.dropna(subset=["weight_kg"])
    tdee = recent["tdee_calories"] if "tdee_calories" in recent else pd.Series(dtype=float)
    def fmt(x, unit=""):
        return "unavailable" if pd.isna(x) else f"{x:,.1f}{unit}"
    weight_change = (observed.weight_kg.iloc[-1] - observed.weight_kg.iloc[0]) if len(observed) >= 2 else float("nan")
    return "\n".join([
        f"# Fitness week ending {end_date.date()}",
        "",
        "## Data quality",
        f"- Days in exported data: {quality['total_days']} (not necessarily all seven calendar days)",
        f"- Food logged: {quality['logged_days']} days",
        f"- Plausibly complete diary: {quality['plausibly_complete_days']} days (heuristic only)",
        f"- Missing/unknown intake: {quality['unknown_intake_days']} exported days",
        f"- Possibly partial food days: {quality['possibly_partial_days']}",
        "",
        "## Recorded and estimated trends",
        f"- Latest exported weight: {fmt(observed.weight_kg.iloc[-1] if not observed.empty else float('nan'), ' kg')}",
        f"- First-to-last exported weight difference: {fmt(weight_change, ' kg')} (repeated values may be carry-forwards)",
        f"- Mean recorded food on plausibly complete days: {fmt(full.calories.mean() if not full.empty else float('nan'), ' kcal')}",
        f"- Mean Withings total-energy estimate: {fmt(tdee.mean() if not tdee.empty else float('nan'), ' kcal')}",
        "",
        "## Next checkpoints",
        "- Check whether the food diary contains missing meals or missing days.",
        "- Confirm whether repeated weight values are new measurements or chart carry-forwards.",
        "- Compare forecasts only after enough complete days have been recorded.",
        "",
        "_Source: local MyFitnessPal and optional Withings exports. Not medical advice._",
        "",
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--end", help="YYYY-MM-DD (defaults to latest recorded date)")
    parser.add_argument("--output", type=Path, help="Optional local .md path under fitness_health/")
    args = parser.parse_args()
    daily, weights = load_mfp(ROOT / "myfitnesspal" / "data")
    activity = load_withings(ROOT / "withings" / "data")
    report = render_report(join_data(daily, weights, activity), args.end)
    if args.output:
        dest = args.output.resolve()
        if not dest.is_relative_to(ROOT):
            parser.error("--output must stay inside fitness_health/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(report, encoding="utf-8")
        print(dest)
    else:
        print(report)


if __name__ == "__main__":
    main()
