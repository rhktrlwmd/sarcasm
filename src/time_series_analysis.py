from __future__ import annotations

import os
import tempfile
import warnings
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tools.sm_exceptions import ValueWarning
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller


def add_regular_time_index(df_metrics: pd.DataFrame, start_date: str, freq: str) -> pd.DataFrame:
    df = df_metrics.copy()
    df["time"] = pd.date_range(start=start_date, periods=len(df), freq=freq)
    return df


def run_adf_test(series: pd.Series) -> dict[str, float | str]:
    clean = prepare_time_series(series).dropna()
    if len(clean) < 5:
        return {
            "adf_statistic": float("nan"),
            "p_value": float("nan"),
            "conclusion": "Недостаточно точек для теста",
        }

    statistic, p_value, *_ = adfuller(clean)
    conclusion = "Стационарный" if p_value < 0.05 else "Нестационарный"
    return {
        "adf_statistic": float(statistic),
        "p_value": float(p_value),
        "conclusion": conclusion,
    }


def add_sma(df_metrics: pd.DataFrame, column: str, window: int) -> pd.DataFrame:
    df = df_metrics.copy()
    df[f"{column}_sma"] = df[column].rolling(window=window, min_periods=1).mean()
    return df


def prepare_time_series(series: pd.Series) -> pd.Series:
    clean = series.dropna().copy()
    if clean.empty:
        return clean

    if isinstance(clean.index, pd.DatetimeIndex):
        freq = clean.index.freq or pd.infer_freq(clean.index) or "D"
        return clean.asfreq(freq)

    return clean


def safe_correlation(left: pd.Series, right: pd.Series) -> float:
    pair = pd.concat([left, right], axis=1).dropna()
    if len(pair) < 2:
        return float("nan")

    left_values = pair.iloc[:, 0]
    right_values = pair.iloc[:, 1]

    if float(left_values.std(ddof=0)) == 0.0 or float(right_values.std(ddof=0)) == 0.0:
        return float("nan")

    return float(left_values.corr(right_values))


def save_metrics_plot(df_metrics: pd.DataFrame, output_path: Path) -> None:
    fig, axes = plt.subplots(4, 2, figsize=(14, 12), sharex=True)
    metric_names = [
        "avg_degree",
        "density",
        "avg_clustering",
        "n_components",
        "diameter",
        "betweenness_mean",
        "betweenness_max",
        "n_events",
    ]

    for axis, metric in zip(axes.flat, metric_names, strict=False):
        axis.plot(df_metrics["time"], df_metrics[metric], marker="o")
        axis.set_title(metric)
        axis.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_sma_plot(df_metrics: pd.DataFrame, column: str, output_path: Path) -> None:
    fig, axis = plt.subplots(figsize=(10, 5))
    axis.plot(df_metrics["time"], df_metrics[column], marker="o", label=column)
    axis.plot(df_metrics["time"], df_metrics[f"{column}_sma"], marker="o", label=f"{column}_sma")
    axis.set_title("Скользящее среднее")
    axis.legend()
    axis.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_decomposition_plot(series: pd.Series, period: int, output_path: Path) -> bool:
    clean = prepare_time_series(series)
    if len(clean) < period * 2:
        return False

    decomposition = seasonal_decompose(clean, model="additive", period=period)
    fig = decomposition.plot()
    fig.set_size_inches(12, 8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return True


def fit_arima(series: pd.Series, order: tuple[int, int, int], forecast_steps: int) -> dict[str, object] | None:
    clean = prepare_time_series(series).astype(float)
    if len(clean) < 10:
        return None

    test_size = max(3, len(clean) // 5)
    if len(clean) - test_size < 8:
        return None

    train = clean.iloc[:-test_size]
    test = clean.iloc[-test_size:]

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ValueWarning)
            train_model = ARIMA(train, order=order).fit()
            test_forecast = pd.Series(train_model.forecast(steps=len(test)), index=test.index)

            full_model = ARIMA(clean, order=order).fit()
            freq = clean.index.freq or pd.infer_freq(clean.index) or "D"
            offset = pd.tseries.frequencies.to_offset(freq)
            future_index = pd.date_range(clean.index[-1] + offset, periods=forecast_steps, freq=freq)
            future_forecast = pd.Series(full_model.forecast(steps=forecast_steps), index=future_index)
    except Exception:
        return None

    mae = float(mean_absolute_error(test, test_forecast))
    mse = float(mean_squared_error(test, test_forecast))
    rmse = float(np.sqrt(mse))

    comparison = pd.DataFrame(
        {
            "actual": test,
            "predicted": test_forecast,
            "abs_error": (test - test_forecast).abs(),
        }
    )

    future = pd.DataFrame({"forecast": future_forecast})

    return {
        "train": train,
        "test": test,
        "test_forecast": test_forecast,
        "future_forecast": future_forecast,
        "comparison": comparison,
        "future": future,
        "mae": mae,
        "rmse": rmse,
    }


def save_forecast_plot(arima_result: dict[str, object], output_path: Path) -> None:
    fig, axis = plt.subplots(figsize=(10, 5))
    train = arima_result["train"]
    test = arima_result["test"]
    test_forecast = arima_result["test_forecast"]
    future_forecast = arima_result["future_forecast"]

    axis.plot(train.index, train.values, label="train")
    axis.plot(test.index, test.values, marker="o", label="actual")
    axis.plot(test_forecast.index, test_forecast.values, marker="o", label="predicted_test")
    axis.plot(future_forecast.index, future_forecast.values, marker="o", linestyle="--", label="forecast_future")
    axis.set_title("Прогноз ARIMA для avg_degree")
    axis.legend()
    axis.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_top_betweenness_plot(
    betweenness_df: pd.DataFrame,
    output_path: Path,
    top_n: int = 5,
) -> pd.DataFrame:
    top_nodes = (
        betweenness_df.groupby("node", as_index=False)["betweenness"]
        .mean()
        .sort_values("betweenness", ascending=False)
        .head(top_n)
        .rename(columns={"betweenness": "mean_betweenness"})
    )
    selected = betweenness_df[betweenness_df["node"].isin(top_nodes["node"])].copy()
    time_column = "time" if "time" in selected.columns else "time_start"
    selected[time_column] = pd.to_datetime(selected[time_column])

    fig, axis = plt.subplots(figsize=(12, 6))
    for node in top_nodes["node"]:
        node_df = selected[selected["node"] == node].sort_values("time_start")
        axis.plot(node_df[time_column], node_df["betweenness"], marker="o", label=str(node))

    axis.set_title("Временные ряды betweenness для наиболее центральных вершин")
    axis.legend()
    axis.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return top_nodes
