"""Reproducible, conservative MyFitnessPal + Withings analytics.

Missing diary records are never interpreted as zero calories consumed.
Withings totalcalories is already a total: never add active calories to it.
"""
from pathlib import Path
import numpy as np
import pandas as pd

KCAL_PER_KG = 7700
GOALS = (84, 82, 80, 78, 76)

def load_mfp(data_dir):
    folder = Path(data_dir)
    daily_files = sorted(folder.glob("*_daily.csv"))
    weight_files = sorted(folder.glob("*weight*.csv"))
    if not daily_files or not weight_files:
        raise FileNotFoundError(f"Expected *_daily.csv and *weight*.csv in {folder}")
    daily = pd.concat([pd.read_csv(f) for f in daily_files], ignore_index=True)
    weight = pd.concat([pd.read_csv(f) for f in weight_files], ignore_index=True)
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce").dt.normalize()
    weight["date"] = pd.to_datetime(weight["date"], errors="coerce").dt.normalize()
    daily = daily.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    weight = weight.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    for field in ("calories", "protein_g", "carbs_g", "fat_g", "food_entries"):
        daily[field] = pd.to_numeric(daily.get(field), errors="coerce")
    weight["weight_kg"] = pd.to_numeric(weight["weight_kg"], errors="coerce")
    daily["logged"] = daily["food_entries"].fillna(0).gt(0)
    daily["possibly_partial"] = daily["logged"] & daily["calories"].lt(1400)
    daily["plausibly_complete"] = daily["logged"] & ~daily["possibly_partial"]
    # Weigh-in export sometimes carries prior measurements forward; flag repeats, not independent readings.
    weight["changed_from_previous"] = weight["weight_kg"].ne(weight["weight_kg"].shift())
    return daily, weight

def load_withings(folder):
    folder = Path(folder)
    path = folder / "withings_daily_activity.csv"
    if not path.exists():
        return pd.DataFrame(columns=["date", "tdee_calories", "active_burned_calories", "steps"])
    activity = pd.read_csv(path)
    activity["date"] = pd.to_datetime(activity["date"], errors="coerce").dt.normalize()
    for orig, normalized in [("totalcalories", "tdee_calories"),
                             ("calories", "active_burned_calories")]:
        if normalized not in activity and orig in activity:
            activity[normalized] = activity[orig]
    for col in ("tdee_calories", "active_burned_calories", "steps"):
        activity[col] = pd.to_numeric(activity.get(col), errors="coerce")
    activity = activity.dropna(subset=["date"]).drop_duplicates("date", keep="last")
    return activity

def join_data(daily, weight, activity):
    frame = daily.merge(weight[["date", "weight_kg", "changed_from_previous"]],
                        on="date", how="outer")
    if not activity.empty:
        frame = frame.merge(activity, on="date", how="outer", suffixes=("", "_withings"))
    frame = frame.sort_values("date").reset_index(drop=True)
    frame["weight_7d_mean"] = frame["weight_kg"].rolling(7, min_periods=3).mean()
    frame["logged"] = frame["logged"].fillna(False).astype(bool)
    frame["plausibly_complete"] = frame["plausibly_complete"].fillna(False).astype(bool)
    # Only compare intake and expenditure on potentially complete logging days.
    frame["observed_deficit_kcal"] = np.where(
        frame["plausibly_complete"], frame.get("tdee_calories", np.nan) - frame["calories"], np.nan)
    return frame

def monthly_summary(frame):
    work = frame.copy()
    work["month"] = work["date"].dt.to_period("M").astype(str)
    return (work.groupby("month").agg(
        days=("date", "size"),
        days_logged=("logged", "sum"),
        plausible_full_days=("plausibly_complete", "sum"),
        mean_logged_kcal=("calories", lambda x: x[x > 0].mean()),
        mean_withings_tdee=("tdee_calories", "mean") if "tdee_calories" in work else ("calories", lambda x: np.nan),
        last_weight_kg=("weight_kg", "last"),
    ).reset_index())

def forecast(start_weight=86.8, start_date="2026-10-20", tdee=2600,
             baseline_intake=1800, extra_meal_kcal=600, meals_weekly=2,
             tdee_per_kg=22, days=800, targets=GOALS):
    """Daily discrete energy-balance scenario; not a clinical prediction."""
    avg_intake = baseline_intake + extra_meal_kcal * meals_weekly / 7
    date = pd.Timestamp(start_date)
    weight = float(start_weight)
    rows = []
    for i in range(days + 1):
        maintenance = tdee + tdee_per_kg * (weight - start_weight)
        deficit = maintenance - avg_intake
        rows.append({"date": date + pd.Timedelta(days=i), "weight_kg": weight,
                     "maintenance_kcal": maintenance, "avg_intake_kcal": avg_intake,
                     "daily_deficit_kcal": deficit})
        if deficit <= 0:
            break
        weight -= deficit / KCAL_PER_KG
    path = pd.DataFrame(rows)
    milestones = pd.DataFrame([
        {"goal_kg": goal,
         "date": path.loc[path["weight_kg"].le(goal), "date"].min()}
        for goal in targets])
    return path, milestones

def lean_goal_table(dexa_ffm=78.021, height_m=1.77):
    rows = []
    for bf in (.10, .08):
        needed = 95 * (1 - bf)
        rows.append({"goal": f"95 kg at {bf:.0%}", "body_fat_pct": bf * 100,
                     "fat_kg": 95 * bf, "required_ffm_kg": needed,
                     "additional_ffm_kg": needed - dexa_ffm,
                     "ffmi": needed / height_m ** 2})
    return pd.DataFrame(rows)
