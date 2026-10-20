# Gym Day workout data

Place the **original** Gym Day / Daily Strength ZIP export in `fitness_health/gymday/data/`. Do not unzip it. The local dashboard reads `WorkoutSession.json` from the most recently modified ZIP.

Raw exports stay on your PC: **do not commit them to GitHub**. You can copy your export from [Google Drive](https://drive.google.com/file/d/19STLjhElQFAOspVafRKNXqoDJHOd1FYF/view).

The training tab includes workout totals, working-set counts, exercise dropdown, best load, estimated Epley 1RM, session volume and working sets, plus recent exercise sessions.

## Run from repository root (PowerShell)

```powershell
git pull origin main
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m fitness_health.local_app
```

Open http://127.0.0.1:8765 and select **Strength training**. Stop with Ctrl+C.

Import rules: completed non-warmup sets only; load converted to kg for lb records, volume = load × reps, Epley e1RM for sets of 1–12 reps. Exercise IDs remain separate even when names overlap. Session dates are UTC. Data is loaded locally on refresh; it is not synchronized with Google Drive automatically.
