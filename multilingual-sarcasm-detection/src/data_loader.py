from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from src.config import PROCESSED_DATASET_PATH, RAW_DATA_PATH
from src.utils import normalize_paths

TEXT_ALIASES = {"text", "headline"}
LABEL_ALIASES = {"label", "is_sarcastic"}


def _read_single_file(file_path: Path) -> pd.DataFrame:
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix == ".json":
        try:
            return pd.read_json(file_path, lines=True)
        except ValueError:
            return pd.read_json(file_path)
    raise ValueError(f"Unsupported file format: {file_path}")


def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    lower_to_original = {column.lower(): column for column in df.columns}

    text_column = next((lower_to_original[name] for name in TEXT_ALIASES if name in lower_to_original), None)
    label_column = next((lower_to_original[name] for name in LABEL_ALIASES if name in lower_to_original), None)

    if text_column:
        rename_map[text_column] = "text"
    if label_column:
        rename_map[label_column] = "label"

    renamed_df = df.rename(columns=rename_map)
    required = {"text", "label"}
    missing = required - set(renamed_df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    return renamed_df[["text", "label"]]


def _normalize_label(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Label cannot be empty")

    normalized = str(value).strip().lower()
    positive_values = {"1", "true", "sarcastic", "yes"}
    negative_values = {"0", "false", "not sarcastic", "not_sarcastic", "non_sarcastic", "no"}

    if normalized in positive_values:
        return 1
    if normalized in negative_values:
        return 0
    if normalized.isdigit():
        numeric_label = int(normalized)
        if numeric_label in {0, 1}:
            return numeric_label
    raise ValueError(f"Unsupported label value: {value}")


def load_data(data_paths: str | Path | Iterable[str | Path] | None = None) -> pd.DataFrame:
    file_paths = normalize_paths(data_paths)
    if not file_paths:
        raise FileNotFoundError(
            f"No CSV or JSON datasets found in {RAW_DATA_PATH}. "
            "Add files with text/label or headline/is_sarcastic columns."
        )

    frames: list[pd.DataFrame] = []
    for file_path in file_paths:
        df = _read_single_file(file_path)
        df = _rename_columns(df)
        df["source_file"] = file_path.name
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    combined["text"] = combined["text"].where(combined["text"].notna(), pd.NA)
    combined["text"] = combined["text"].apply(lambda value: value.strip() if isinstance(value, str) else value)
    combined["label"] = combined["label"].apply(_normalize_label)
    combined = combined.replace({"text": {"": pd.NA}})
    combined = combined.dropna(subset=["text", "label"])
    combined = combined.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)
    return combined


def save_processed_data(df: pd.DataFrame, output_path: Path = PROCESSED_DATASET_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def load_processed_data(input_path: Path = PROCESSED_DATASET_PATH) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(f"Processed dataset not found: {input_path}")
    return pd.read_csv(input_path)
