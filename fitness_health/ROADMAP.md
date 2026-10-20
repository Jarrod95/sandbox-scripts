# Fitness & Health — Development Roadmap

> **Status:** proposed, not implemented. **Last updated:** 2026-10-20.  
> **Scope boundary:** All fitness and personal-health scripts, data, reports, notebooks, tests and dashboards live under `fitness_health/`. The repository root remains a generic sandbox for unrelated scripts. Never move fitness datasets back to root.

## Purpose and operating principles

Build a reproducible, privacy-conscious, evidence-based fitness analytics platform that explains historical trends, calibrates energy expenditure, tracks training and health, and forecasts weight and body composition with uncertainty. Keep observed data, wearable estimates, clinical measurements and model assumptions explicitly distinct.

**Non-negotiable rules for future ChatGPT/coding agents**
1. Inspect the repository and this roadmap before editing. Preserve existing working exporters and outputs.
2. **All fitness data remains inside `fitness_health/`**, including new CSV, JSON, XLSX, database files, DEXA exports and generated reports. Do not create `data/`, `myfitnesspal/` or `withings/` at repository root.
3. Use paths relative to the repository or `fitness_health/`; no hard-coded usernames or absolute Windows paths in analysis code. The browser folder picker can show an example destination but must require user approval.
4. Do not commit `.env`, OAuth tokens, credentials, raw clinical records or new sensitive exports. Prefer encrypted/private storage and review historic tracked data exposure.
5. Keep a single canonical calculation for each metric; notebooks, reports and dashboards import the same tested functions.
6. Missing food diary records mean **unknown intake**, not zero. Repeated weight values may be chart carry-forwards. Withings `totalcalories` already includes active energy.
7. DEXA and EVOLT/BIA are different methods. Never equate fat-free mass with skeletal muscle or imply long-term muscle-gain forecasts are guarantees.
8. For each change, add tests, document assumptions, and run smoke checks where possible. If private API execution cannot be performed, say so in the PR.
9. Keep README files concise; detailed design, decisions and the backlog belong here. Open PRs; do not merge without review.

## Current baseline (October 2026)

- `fitness_health/myfitnesspal/`: browser food diary and weight exporters, CSV/JSON history, weight journey notebook and shareable `WEIGHT_JOURNEY.md`.
- `fitness_health/withings/`: API extraction notebook for activity, workouts, measurements, sleep and heart event metadata.
- `fitness_health/fitness_analysis.py`: shared food/weight cleaning, optional wearable joins, TDEE sensitivity scenarios and DEXA-based goal calculations.
- Root: generic README, dependency manifest, `.gitignore` and an untracked local `.env` (with `CLIENT_ID` and `CLIENT_SECRET`). No fitness data belongs at root.

## Prioritized backlog

| ID | Priority | Workstream | Deliverable | Acceptance criteria |
| --- | --- | --- | --- | --- |
| FH-01 | P0 | Security | Review repo visibility and history of committed health exports | Sensitive data no longer publicly exposed; secret scanning and history remediation assessed |
| FH-02 | P0 | Paths | Verify every moved notebook, JS exporter and README | Run from root and subfolders; no references to old root-level fitness paths |
| FH-03 | P0 | Quality | Schema, date, unit and completeness validation | Tests cover missing diary days, duplicates, carry-forward weights, partial days and malformed API payloads |
| FH-04 | P0 | CI | GitHub Actions: lint, tests, notebook parse/smoke checks | PR checks pass without credentials or private health data |
| FH-05 | P1 | Withings | Incremental API ingestion, refresh handling and audit log | Idempotent exports; missing scopes/devices reported; retries/rate limits handled |
| FH-06 | P1 | MyFitnessPal | More robust repeatable exports and import manifest | Files land only under `fitness_health/myfitnesspal/data`; stable filenames and de-duplication |
| FH-07 | P1 | TDEE | Wearable vs weight/intake-derived rolling estimate | Uncertainty bands, incomplete-day exclusions and out-of-sample accuracy tracking |
| FH-08 | P1 | Training | Strength training schema and importer | Exercise, sets, reps, load, RPE/RIR, volume, estimated 1RM and weekly summaries |
| FH-09 | P1 | Dashboard | Streamlit app with overview, diet, weight and TDEE | Readable high-contrast graphs; filters; provenance shown; no data leaves private storage |
| FH-10 | P1 | Reports | Weekly automated summary | Trends, completeness, model error, next checkpoints and actionable questions |
| FH-11 | P2 | Composition | DEXA and BIA longitudinal module | Separate method series, FFMI, fat/lean mass, confidence and measurement conditions |
| FH-12 | P2 | Nutrition | Macro, fibre and micronutrient adequacy | Completeness-aware trends; no invented intake for unlogged days |
| FH-13 | P2 | Recovery | Sleep, resting HR, activity and subjective fatigue | Source/device availability flags and longitudinal comparisons |
| FH-14 | P2 | Health | Blood pressure, lipid, blood count and clinical marker history | Private storage, reference ranges, clinician review guidance; no automatic medical clearance |
| FH-15 | P2 | Forecasts | Dynamic energy-balance model and scenario explorer | User-selectable maintenance date, activity, calories and composition assumptions; prediction intervals |
| FH-16 | P3 | Platform | Internal health-data API and database | Versioned schemas, documented contracts, authenticated local access |
| FH-17 | P3 | Research | Evaluate statistical/predictive methods | Backtests against held-out periods; compare against simple baselines; no overfitting |

## Recommended target layout

```text
sandbox-scripts/
├── README.md                         # generic sandbox index
├── .gitignore
├── requirements.txt                  # or workspace-level dependency management
├── .env.example
├── fitness_health/
│   ├── README.md
│   ├── ROADMAP.md                     # this document
│   ├── fitness_analysis.py           # existing shared calculations; refactor later
│   ├── myfitnesspal/
│   │   ├── data/                      # ALL MFP exports
│   │   ├── mfp-fooddiary.js
│   │   ├── mfp-weight-history.js
│   │   ├── weight_journey.ipynb
│   │   └── WEIGHT_JOURNEY.md
│   ├── withings/
│   │   ├── data/                      # ALL Withings exports
│   │   └── withings-mfp-calories.ipynb
│   ├── src/fitness/                   # future reusable Python package
│   │   ├── ingestion/
│   │   ├── validation/
│   │   ├── models/
│   │   └── reporting/
│   ├── dashboards/
│   ├── notebooks/
│   ├── tests/
│   ├── reports/
│   └── data/                          # future OTHER fitness data only
└── other_script_projects/            # unrelated work
```

The layout under `src/` is aspirational. Don't create empty directories or migrate code without a concrete feature or test.

## Milestone sequence

### Sprint 1 — reliable foundation
- [ ] FH-01: private data and secrets review
- [ ] FH-02: test relocated notebooks and browser exporters
- [ ] FH-03: data quality tests
- [ ] FH-04: CI checks

**Definition of done:** reproducible imports, no broken paths, documented coverage, no credentials in commits, passing automated tests.

### Sprint 2 — continuous ingestion and better TDEE
- [ ] FH-05: Withings incremental extraction
- [ ] FH-06: MyFitnessPal import manifests
- [ ] FH-07: rolling TDEE model with uncertainty

**Definition of done:** rerunning ingestion is idempotent, errors are observable, and TDEE estimates can be compared with observed weight/intake trends.

### Sprint 3 — training and reporting
- [ ] FH-08: training logs
- [ ] FH-09: Streamlit dashboard
- [ ] FH-10: weekly summary

**Definition of done:** weight, food, activity and lifting data appear together, with labelled source coverage and accessible plots.

### Sprint 4 — body composition and clinical context
- [ ] FH-11 through FH-15
- [ ] DEXA refresh near April 2027, as appropriate
- [ ] Assess the feasibility and health implications of the 95 kg at 10% and 8% aspirations

**Definition of done:** longitudinal composition metrics distinguish methods; forecasts show scenarios rather than guaranteed dates; health markers are reviewed appropriately.

## Analytics contracts and definitions

| Field | Definition | Caveat |
| --- | --- | --- |
| `weight_kg` | Actual recorded weigh-in where identifiable | Carry-forward chart values are not new measurements |
| `calories` | Food diary recorded kcal | Unlogged/partial days must not be treated as true total intake |
| `tdee_calories` | Withings `totalcalories` | Estimated total expenditure, not independently measured |
| `active_burned_calories` | Withings active-energy estimate | Subset of total; never add to `tdee_calories` |
| `fat_free_mass_kg` | DEXA lean soft tissue + bone mineral | Includes non-muscle tissues and fluid |
| `ffmi` | Fat-free mass divided by height squared | Requires consistent measurement method |
| `forecast_weight_kg` | Scenario output | Must record assumptions, version, run date and uncertainty |

**Reference scenarios from prior analysis:** latest historical weight ~86.8 kg (October 2026); provisional TDEE ~2,600 kcal/day with 2,450–2,750 sensitivity; September DEXA fat-free mass ~78.021 kg; 95 kg at 10% requires 85.5 kg FFM and 95 kg at 8% requires 87.4 kg. These are historical planning inputs, not fresh observations.

## How to request a future implementation PR

Paste this roadmap into a ChatGPT conversation and request:

> Implement **FH-XX** from `fitness_health/ROADMAP.md` in `Jarrod95/sandbox-scripts`. Inspect the current implementation first. Keep all fitness files and data within `fitness_health/`. Reuse existing functions; add automated tests and concise documentation; update the relevant roadmap checklist; open a PR without merging. Report any checks you could not run.

## What good looks like

- One reproducible, tested source of truth for each metric.
- A clean separation between ingestion, validation, modelling and presentation.
- No personal health datasets outside `fitness_health/`, and no credentials in version control.
- Clear observed-versus-estimated-versus-forecast labels and uncertainty ranges.
- Readable dashboards and reports, without duplicate calculations.
- Each PR implements a bounded roadmap item, has tests, and documents data limitations.
