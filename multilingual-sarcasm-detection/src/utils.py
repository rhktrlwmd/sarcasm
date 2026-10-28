from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from src.config import PROCESSED_DATA_PATH, PROJECT_ROOT, RAW_DATA_PATH, RESULTS_PATH


def ensure_directories(paths: Iterable[Path]) -> None:
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def list_dataset_files(raw_data_path: Path = RAW_DATA_PATH) -> list[Path]:
    if not raw_data_path.exists():
        return []

    supported_files = []
    for extension in ("*.csv", "*.json"):
        supported_files.extend(sorted(raw_data_path.rglob(extension)))
    return supported_files


def save_json(data: dict, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_json(input_path: Path, default: dict | None = None) -> dict:
    if not input_path.exists():
        return {} if default is None else default
    with input_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_paths(data_paths: str | Path | Iterable[str | Path] | None) -> list[Path]:
    if data_paths is None:
        return list_dataset_files()
    if isinstance(data_paths, (str, Path)):
        return [Path(data_paths)]
    return [Path(path) for path in data_paths]


def bootstrap_project_directories() -> None:
    ensure_directories(
        [
            RAW_DATA_PATH,
            PROCESSED_DATA_PATH,
            PROCESSED_DATA_PATH / "plots",
            PROCESSED_DATA_PATH / "predictions",
            RESULTS_PATH,
            PROJECT_ROOT / "models",
        ]
    )
