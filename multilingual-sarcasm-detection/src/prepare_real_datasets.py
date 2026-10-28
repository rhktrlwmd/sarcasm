from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import PROJECT_ROOT
from src.utils import ensure_directories

EXTERNAL_DATA_PATH = PROJECT_ROOT / "data" / "external"
REAL_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "real"

ENGLISH_SOURCE = EXTERNAL_DATA_PATH / "en_sarcasm_headlines_v2.json"
RUSSIAN_SATIRE_SOURCE = EXTERNAL_DATA_PATH / "ru_panorama.jsonl"
RUSSIAN_NEWS_SOURCE = EXTERNAL_DATA_PATH / "ru_news_train.parquet"
RUSSIAN_NEWS_FALLBACK_SOURCE = EXTERNAL_DATA_PATH / "ru_ria_1k.json"
RUSSIAN_MANUAL_CONVERSATIONAL_SOURCE = REAL_DATA_PATH / "manual_ru_conversational_reddit.csv"

ENGLISH_OUTPUT = REAL_DATA_PATH / "real_english_sarcasm_headlines.csv"
RUSSIAN_SATIRE_OUTPUT = REAL_DATA_PATH / "real_russian_panorama_sarcasm.csv"
RUSSIAN_NEWS_OUTPUT = REAL_DATA_PATH / "real_russian_news_nonsarcastic.csv"


def _read_json_dataset(dataset_path: Path) -> pd.DataFrame:
    try:
        return pd.read_json(dataset_path, lines=True)
    except ValueError:
        return pd.read_json(dataset_path)


def _first_sentence(text: object, max_length: int = 220) -> str:
    if text is None:
        return ""
    value = str(text).strip()
    if not value:
        return ""

    for delimiter in (". ", "! ", "? ", "… ", "\n"):
        if delimiter in value:
            sentence = value.split(delimiter, 1)[0].strip()
            if sentence:
                return sentence[:max_length]
    return value[:max_length].strip()


def prepare_real_datasets(include_manual_russian_conversational: bool = True) -> list[Path]:
    ensure_directories([REAL_DATA_PATH])

    if not ENGLISH_SOURCE.exists():
        raise FileNotFoundError(f"English source dataset not found: {ENGLISH_SOURCE}")
    if not RUSSIAN_SATIRE_SOURCE.exists():
        raise FileNotFoundError(f"Russian satire source dataset not found: {RUSSIAN_SATIRE_SOURCE}")
    if not RUSSIAN_NEWS_SOURCE.exists() and not RUSSIAN_NEWS_FALLBACK_SOURCE.exists():
        raise FileNotFoundError(
            "Russian news source dataset not found. Expected either "
            f"{RUSSIAN_NEWS_SOURCE} or {RUSSIAN_NEWS_FALLBACK_SOURCE}."
        )

    english_df = _read_json_dataset(ENGLISH_SOURCE)
    english_df = english_df.rename(columns={"headline": "text", "is_sarcastic": "label"})
    english_df = english_df[["text", "label"]].dropna()
    english_df["text"] = english_df["text"].astype(str).str.strip()
    english_df["label"] = english_df["label"].astype(int)
    english_df = english_df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)
    if len(english_df) > 12000:
        english_df = english_df.sample(n=12000, random_state=42).reset_index(drop=True)
    english_df.to_csv(ENGLISH_OUTPUT, index=False, encoding="utf-8")

    russian_satire_df = pd.read_json(RUSSIAN_SATIRE_SOURCE, lines=True)
    russian_satire_df["text"] = russian_satire_df["title"].astype(str).str.strip()
    russian_satire_df["label"] = 1
    russian_satire_df = russian_satire_df[["text", "label"]]
    russian_satire_df = russian_satire_df.replace({"text": {"": pd.NA}}).dropna()
    russian_satire_df = russian_satire_df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)

    try:
        russian_news_df = pd.read_parquet(RUSSIAN_NEWS_SOURCE)
        russian_news_df["text"] = russian_news_df["text"].apply(_first_sentence)
    except Exception:
        if not RUSSIAN_NEWS_FALLBACK_SOURCE.exists():
            raise
        russian_news_df = _read_json_dataset(RUSSIAN_NEWS_FALLBACK_SOURCE)
        if "title" in russian_news_df.columns:
            russian_news_df["text"] = russian_news_df["title"].astype(str).str.strip()
        else:
            russian_news_df["text"] = russian_news_df["text"].apply(_first_sentence)

    russian_news_df["label"] = 0
    russian_news_df = russian_news_df[["text", "label"]]
    russian_news_df = russian_news_df.replace({"text": {"": pd.NA}}).dropna()
    russian_news_df = russian_news_df.drop_duplicates(subset=["text", "label"]).reset_index(drop=True)

    # Keep the Russian classes roughly balanced so English does not dominate the coursework baseline.
    russian_satire_df = russian_satire_df.sample(
        n=min(len(russian_satire_df), len(russian_news_df)),
        random_state=42,
    ).reset_index(drop=True)
    russian_news_df = russian_news_df.sample(
        n=min(len(russian_news_df), len(russian_satire_df)),
        random_state=42,
    ).reset_index(drop=True)

    russian_satire_df.to_csv(RUSSIAN_SATIRE_OUTPUT, index=False, encoding="utf-8")
    russian_news_df.to_csv(RUSSIAN_NEWS_OUTPUT, index=False, encoding="utf-8")

    dataset_paths = [ENGLISH_OUTPUT, RUSSIAN_SATIRE_OUTPUT, RUSSIAN_NEWS_OUTPUT]
    if include_manual_russian_conversational and RUSSIAN_MANUAL_CONVERSATIONAL_SOURCE.exists():
        dataset_paths.append(RUSSIAN_MANUAL_CONVERSATIONAL_SOURCE)

    return dataset_paths


if __name__ == "__main__":
    outputs = prepare_real_datasets()
    for path in outputs:
        print(path)
