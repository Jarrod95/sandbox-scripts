"""Completeness and schema checks that never invent missing food records."""
from __future__ import annotations

import pandas as pd


def audit_frame(frame: pd.DataFrame) -> dict:
    required = {"date", "calories", "logged", "plausibly_complete", "weight_kg"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError("Missing columns: " + ", ".join(sorted(missing)))
    if frame.date.isna().any() or frame.date.duplicated().any():
        raise ValueError("Daily frame has null or duplicate dates.")
    calories = pd.to_numeric(frame["calories"], errors="coerce")
    weight = pd.to_numeric(frame["weight_kg"], errors="coerce")
    invalid_calories = int((calories < 0).sum())
    invalid_weight = int(((weight < 20) | (weight > 500)).sum())
    if invalid_calories or invalid_weight:
        raise ValueError(f"Invalid values: calories={invalid_calories}, weight={invalid_weight}")
    logged = frame.logged.fillna(False).astype(bool)
    complete = frame.plausibly_complete.fillna(False).astype(bool)
    if (complete & ~logged).any():
        raise ValueError("A plausibly complete day must be logged.")
    tdee = pd.to_numeric(frame["tdee_calories"], errors="coerce") if "tdee_calories" in frame else pd.Series(float("nan"), index=frame.index)
    return {
        "total_days": len(frame),
        "logged_days": int(logged.sum()),
        "unknown_intake_days": int((~logged).sum()),
        "plausibly_complete_days": int(complete.sum()),
        "possibly_partial_days": int((logged & ~complete).sum()),
        "weight_rows": int(weight.notna().sum()),
        "withings_tdee_days": int(tdee.notna().sum()),
    }
