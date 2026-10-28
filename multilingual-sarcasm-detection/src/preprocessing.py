from __future__ import annotations

import re

import pandas as pd

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", flags=re.IGNORECASE)
MULTISPACE_PATTERN = re.compile(r"\s+", flags=re.UNICODE)
PUNCTUATION_PATTERN = re.compile(r"[^\w\s]", flags=re.UNICODE)


def prepare_text_for_model(text: object) -> str:
    text = "" if text is None else str(text)
    text = URL_PATTERN.sub(" ", text)
    text = MULTISPACE_PATTERN.sub(" ", text)
    return text.strip()


def clean_text(text: object) -> str:
    text = prepare_text_for_model(text).lower()
    text = PUNCTUATION_PATTERN.sub(" ", text)
    text = MULTISPACE_PATTERN.sub(" ", text)
    return text.strip()


def preprocess_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    processed = df.copy()
    processed["model_text"] = processed["text"].apply(prepare_text_for_model)
    processed["clean_text"] = processed["text"].apply(clean_text)
    processed = processed.replace({"model_text": {"": pd.NA}, "clean_text": {"": pd.NA}})
    processed = processed.dropna(subset=["model_text", "clean_text"]).reset_index(drop=True)
    return processed
