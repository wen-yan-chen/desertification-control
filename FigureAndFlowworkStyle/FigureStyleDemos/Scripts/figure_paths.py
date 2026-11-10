"""Resolve all demo outputs into the common Images directory."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent.parent
FIGURE_ROOT = ROOT / "Images"
CATALOG = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
CATEGORIES = {(entry["source"], entry["name"]): entry["category"] for entry in CATALOG}


def output_path(source, name, extension):
    """Keep known chart names classified; route new names to custom outputs."""
    category = CATEGORIES.get((source, name), "06_自定义输出")
    directory = FIGURE_ROOT / category
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{source}_{name}.{extension}"
