from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import SarcasmProjectConfig

TEXT_ALIASES = (
    "text",
    "tweet",
    "comment",
    "post",
    "caption",
    "content",
    "sentence",
    "utterance",
)
LABEL_ALIASES = ("label", "sarcasm", "is_sarcastic", "class", "target")
PLATFORM_ALIASES = ("platform", "source_platform", "network")

POSITIVE_LABELS = {"1", "true", "yes", "sarcastic", "sarcasm", "ironic", "irony"}
NEGATIVE_LABELS = {"0", "false", "no", "not_sarcastic", "non_sarcastic", "literal", "regular"}


def infer_platform_from_path(path: Path) -> str:
    lowered = path.stem.lower()
    for platform in ("twitter", "reddit", "facebook", "instagram"):
        if platform in lowered:
            return platform
    if "tweet" in lowered or "x_" in lowered or lowered.startswith("x"):
        return "twitter"
    return "unknown"


def _pick_column(columns: list[str], aliases: tuple[str, ...]) -> str | None:
    normalized = {column.lower(): column for column in columns}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def normalize_label(value: object) -> int | None:
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)) and value in (0, 1):
        return int(value)

    text = str(value).strip().lower().replace(" ", "_")
    if text in POSITIVE_LABELS:
        return 1
    if text in NEGATIVE_LABELS:
        return 0
    return None


def normalize_dataset(frame: pd.DataFrame, source_path: Path) -> pd.DataFrame:
    working = frame.copy()
    columns = list(working.columns)

    text_column = _pick_column(columns, TEXT_ALIASES)
    label_column = _pick_column(columns, LABEL_ALIASES)
    platform_column = _pick_column(columns, PLATFORM_ALIASES)

    if text_column is None or label_column is None:
        raise ValueError(
            f"Dataset {source_path.name} must contain a text column and a label column. "
            f"Supported text aliases: {TEXT_ALIASES}; label aliases: {LABEL_ALIASES}."
        )

    default_platform = infer_platform_from_path(source_path)
    normalized = pd.DataFrame(
        {
            "text": working[text_column].astype(str),
            "label": working[label_column].map(normalize_label),
            "platform": (
                working[platform_column].astype(str).str.lower()
                if platform_column is not None
                else default_platform
            ),
            "source_dataset": source_path.name,
        }
    )

    normalized["platform"] = normalized["platform"].fillna(default_platform).replace("", default_platform)
    normalized = normalized.dropna(subset=["text", "label"])
    normalized["text"] = normalized["text"].str.strip()
    normalized = normalized[normalized["text"] != ""].copy()
    normalized["label"] = normalized["label"].astype(int)
    normalized["platform"] = normalized["platform"].astype(str).str.lower()
    return normalized.reset_index(drop=True)


def load_all_datasets(
    config: SarcasmProjectConfig,
    dataset_dir: Path | None = None,
) -> tuple[pd.DataFrame, list[Path]]:
    raw_dir = dataset_dir or config.raw_data_dir
    csv_files = sorted(raw_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {raw_dir}. "
            "Add at least one dataset with columns like text/label/platform."
        )

    frames: list[pd.DataFrame] = []
    for csv_file in csv_files:
        frame = pd.read_csv(csv_file)
        frames.append(normalize_dataset(frame, csv_file))

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["text", "platform", "label"]).reset_index(drop=True)
    return combined, csv_files


def build_stratify_labels(dataset: pd.DataFrame) -> pd.Series:
    compound = dataset["platform"].astype(str) + "__" + dataset["label"].astype(str)
    if int(compound.value_counts().min()) >= 2:
        return compound
    return dataset["label"]


def save_dataset_summary(dataset: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    summary = (
        dataset.groupby(["platform", "label"], as_index=False)
        .size()
        .rename(columns={"size": "samples"})
        .sort_values(["platform", "label"])
    )
    summary.to_csv(output_path, index=False)
    return summary
