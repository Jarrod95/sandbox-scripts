from pathlib import Path
from zipfile import ZipFile

root = Path.cwd()
archive = root / "longevitynet-source.zip"
destination = root / "longevitynet"

if not archive.is_file():
    raise FileNotFoundError(f"ZIP archive not found: {archive}")

with ZipFile(archive) as z:
    count = 0

    for entry in z.infolist():
        if entry.is_dir():
            continue

        relative = entry.filename.removeprefix("longevitynet-main/")

        allowed = (
            relative in {"__init__.py", "requirements.txt"}
            or relative.startswith("deployment/")
            or relative.startswith("modelling/")
        )

        if not allowed:
            continue

        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)

        with z.open(entry) as source, target.open("wb") as output:
            import shutil
            shutil.copyfileobj(source, output)

        count += 1
        print(f"Extracted: {relative}")

print(f"\nSuccessfully extracted {count} files.")
