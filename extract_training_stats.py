from pathlib import Path
from zipfile import ZipFile
import re
import json
import statistics

archive = Path("longevitynet-source.zip")
pattern = re.compile(r"_death:(\d{4})_data:(\d{4})_")

remaining = []

with ZipFile(archive) as z:
    for name in z.namelist():
        if "/datasets/dataset_v5/" not in name or not name.endswith(".jpg"):
            continue

        match = pattern.search(name)
        if match:
            death_year, photo_year = map(int, match.groups())
            remaining.append(death_year - photo_year)

if not remaining:
    raise RuntimeError("No dataset_v5 filenames found in ZIP.")

mean_remaining = statistics.mean(remaining)
deltas = [years - mean_remaining for years in remaining]

result = {
    "dataset": "v5",
    "samples": len(remaining),
    "mean_life_expectancy": mean_remaining,
    "min_delta": min(deltas),
    "max_delta": max(deltas),
}

output = Path("longevitynet") / "deployment" / "training_stats.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result, indent=2), encoding="utf-8")

print(json.dumps(result, indent=2))
print(f"Saved: {output}")
