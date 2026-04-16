from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import LabConfig


def generate_synthetic_events(config: LabConfig) -> pd.DataFrame:
    rng = np.random.default_rng(config.seed)
    nodes = [f"N{i}" for i in range(1, config.n_nodes + 1)]
    timestamps = pd.date_range(config.start_date, periods=config.n_steps, freq=config.frequency)
    records: list[dict[str, object]] = []

    for step, timestamp in enumerate(timestamps):
        progress = step / max(config.n_steps - 1, 1)
        trend = 0.08 + 0.30 * progress
        season = 0.12 * np.sin(2 * np.pi * step / config.synthetic_cycle)
        edge_probability = float(np.clip(trend + season, 0.02, 0.90))

        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if rng.random() < edge_probability:
                    records.append(
                        {
                            "source": nodes[i],
                            "target": nodes[j],
                            "timestamp": timestamp,
                            "step": step,
                        }
                    )

    if not records:
        return pd.DataFrame(columns=["source", "target", "timestamp", "step"])

    return pd.DataFrame(records)


def load_events_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    required_columns = {"source", "target", "timestamp"}
    missing = required_columns.difference(df.columns)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"Missing required columns: {missing_text}")

    return _normalize_events(df)


def load_events_file(path: Path) -> pd.DataFrame:
    suffixes = set(path.suffixes)
    if ".csv" in suffixes:
        return load_events_csv(path)

    df = pd.read_csv(
        path,
        sep=r"\s+",
        header=None,
        names=["source", "target", "timestamp"],
        usecols=[0, 1, 2],
        compression="infer",
    )
    return _normalize_events(df)


def _normalize_events(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp"] = _parse_timestamp(df["timestamp"])
    df = df.dropna(subset=["source", "target", "timestamp"])
    df["source"] = df["source"].astype(str)
    df["target"] = df["target"].astype(str)
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def _parse_timestamp(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    numeric_ratio = float(numeric.notna().mean()) if len(series) else 0.0

    if numeric_ratio > 0.95:
        clean_numeric = numeric.dropna()
        if not clean_numeric.empty:
            median_value = float(clean_numeric.median())
            if 100_000_000 <= median_value <= 20_000_000_000:
                return pd.to_datetime(numeric, unit="s", errors="coerce")

    return pd.to_datetime(series, errors="coerce")
