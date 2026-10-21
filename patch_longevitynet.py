from pathlib import Path

server = Path("longevitynet/deployment/server.py")
source = server.read_text(encoding="utf-8")

old_import = "from longevitynet.modelling.data import get_dataset_dict"
old_dataset = '''dataset_dict = get_dataset_dict(CONFIG)
train_dataset = dataset_dict["datasets"]["train"]'''
old_conversion = "return convert_prediction_to_years(raw_prediction, train_dataset)"

for expected in (old_import, old_dataset, old_conversion):
    if expected not in source:
        raise RuntimeError(f"Expected source not found:\n{expected}")

source = source.replace(
    old_import,
    "import json"
)

source = source.replace(
    old_dataset,
    '''_STATS_PATH = Path(get_repo_dir()) / "deployment" / "training_stats.json"
with _STATS_PATH.open("r", encoding="utf-8") as f:
    training_stats = json.load(f)

assert training_stats["dataset"] == "v5"
assert training_stats["samples"] == 8177'''
)

source = source.replace(
    old_conversion,
    '''return (
        raw_prediction
        * (training_stats["max_delta"] - training_stats["min_delta"])
        + training_stats["min_delta"]
        + training_stats["mean_life_expectancy"]
    )'''
)

server.write_text(source, encoding="utf-8")
print("Server patched successfully.")
