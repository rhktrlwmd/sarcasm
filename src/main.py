from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .config import LabConfig
from .data_loader import generate_synthetic_events, load_events_file
from .graph_metrics import compute_metrics_table
from .time_series_analysis import (
    add_regular_time_index,
    add_sma,
    fit_arima,
    prepare_time_series,
    run_adf_test,
    safe_correlation,
    save_decomposition_plot,
    save_forecast_plot,
    save_metrics_plot,
    save_sma_plot,
    save_top_betweenness_plot,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lab 07 graph and time series analytics")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to events file: CSV with source,target,timestamp or SNAP TXT/TXT.GZ",
    )
    parser.add_argument(
        "--window-size",
        type=int,
        default=None,
        help="Number of events per window",
    )
    parser.add_argument(
        "--synthetic",
        action="store_true",
        help="Use synthetic data instead of a real dataset",
    )
    return parser.parse_args()


def ensure_directories(config: LabConfig) -> None:
    config.raw_dir.mkdir(parents=True, exist_ok=True)
    config.processed_dir.mkdir(parents=True, exist_ok=True)
    config.plots_dir.mkdir(parents=True, exist_ok=True)
    config.report_dir.mkdir(parents=True, exist_ok=True)


def save_summary(
    output_path: Path,
    source_name: str,
    window_size: str,
    undirected_metrics: pd.DataFrame,
    directed_metrics: pd.DataFrame,
    adf_avg_degree: dict[str, float | str],
    adf_in_out_ratio: dict[str, float | str],
    adf_top_betweenness: dict[str, float | str],
    top_betweenness_node: str,
    correlation: float,
    arima_result: dict[str, object] | None,
    decomposition_ready: bool,
) -> None:
    lines = [
        "Лабораторная работа №7",
        f"Источник данных: {source_name}",
        f"Размер окна: {window_size}",
        f"Количество окон: {len(undirected_metrics)}",
        "",
        "ADF для avg_degree:",
        f"  statistic = {adf_avg_degree['adf_statistic']}",
        f"  p_value = {adf_avg_degree['p_value']}",
        f"  conclusion = {adf_avg_degree['conclusion']}",
        "",
        "ADF для in_out_ratio_mean:",
        f"  statistic = {adf_in_out_ratio['adf_statistic']}",
        f"  p_value = {adf_in_out_ratio['p_value']}",
        f"  conclusion = {adf_in_out_ratio['conclusion']}",
        "",
        f"ADF для betweenness вершины {top_betweenness_node}:",
        f"  statistic = {adf_top_betweenness['adf_statistic']}",
        f"  p_value = {adf_top_betweenness['p_value']}",
        f"  conclusion = {adf_top_betweenness['conclusion']}",
        "",
        f"Корреляция avg_degree и n_components: {correlation}",
        f"Декомпозиция построена: {'да' if decomposition_ready else 'нет'}",
    ]

    if arima_result is not None:
        lines.extend(
            [
                "",
                "ARIMA:",
                f"  MAE = {arima_result['mae']}",
                f"  RMSE = {arima_result['rmse']}",
            ]
        )
    else:
        lines.extend(["", "ARIMA: недостаточно данных для устойчивого обучения"])

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    config = LabConfig()
    ensure_directories(config)

    input_path = args.input or config.default_input_path
    window_size = int(args.window_size or config.window_size)

    if args.synthetic:
        events = generate_synthetic_events(config)
        source_name = "synthetic"
    else:
        events = load_events_file(input_path)
        source_name = str(input_path)

    all_nodes = sorted(set(events["source"]).union(set(events["target"])))
    events.to_csv(config.processed_dir / "events_used.csv", index=False)

    metrics_undirected, betweenness_undirected = compute_metrics_table(
        events,
        window_size=window_size,
        directed=False,
        all_nodes=all_nodes,
    )
    metrics_undirected = add_regular_time_index(metrics_undirected, config.start_date, config.frequency)
    metrics_undirected = add_sma(metrics_undirected, "avg_degree", config.sma_window)
    metrics_undirected.to_csv(config.processed_dir / "metrics_undirected.csv", index=False)

    metrics_directed, _ = compute_metrics_table(
        events,
        window_size=window_size,
        directed=True,
        all_nodes=all_nodes,
    )
    metrics_directed = add_regular_time_index(metrics_directed, config.start_date, config.frequency)
    metrics_directed.to_csv(config.processed_dir / "metrics_directed.csv", index=False)

    betweenness_undirected = betweenness_undirected.merge(
        metrics_undirected[["window_id", "time"]],
        on="window_id",
        how="left",
    )
    betweenness_undirected.to_csv(config.processed_dir / "betweenness_by_node.csv", index=False)

    save_metrics_plot(metrics_undirected, config.plots_dir / "metrics_timeseries.png")
    save_sma_plot(metrics_undirected, "avg_degree", config.plots_dir / "sma.png")
    top_betweenness_nodes = save_top_betweenness_plot(
        betweenness_undirected,
        config.plots_dir / "betweenness_top_nodes.png",
    )
    top_betweenness_nodes.to_csv(config.processed_dir / "top_betweenness_nodes.csv", index=False)

    avg_degree_series = prepare_time_series(metrics_undirected.set_index("time")["avg_degree"])
    decomposition_ready = save_decomposition_plot(
        avg_degree_series,
        config.seasonal_period,
        config.plots_dir / "decomposition.png",
    )
    adf_avg_degree = run_adf_test(avg_degree_series)

    in_out_series = prepare_time_series(metrics_directed.set_index("time")["in_out_ratio_mean"])
    adf_in_out_ratio = run_adf_test(in_out_series)

    top_node = str(top_betweenness_nodes.iloc[0]["node"])
    top_node_df = betweenness_undirected[betweenness_undirected["node"].astype(str) == top_node].sort_values("time_start")
    top_node_series = top_node_df.set_index(pd.to_datetime(top_node_df["time"]))["betweenness"]
    adf_top_betweenness = run_adf_test(top_node_series)

    correlation = safe_correlation(metrics_undirected["avg_degree"], metrics_undirected["n_components"])

    arima_result = fit_arima(avg_degree_series, config.arima_order, config.forecast_steps)
    if arima_result is not None:
        save_forecast_plot(arima_result, config.plots_dir / "arima_forecast.png")
        arima_result["comparison"].to_csv(config.processed_dir / "arima_test_comparison.csv", index_label="time")
        arima_result["future"].to_csv(config.processed_dir / "arima_future_forecast.csv", index_label="time")

    save_summary(
        config.outputs_dir / "summary.txt",
        source_name=source_name,
        window_size=window_size,
        undirected_metrics=metrics_undirected,
        directed_metrics=metrics_directed,
        adf_avg_degree=adf_avg_degree,
        adf_in_out_ratio=adf_in_out_ratio,
        adf_top_betweenness=adf_top_betweenness,
        top_betweenness_node=top_node,
        correlation=correlation,
        arima_result=arima_result,
        decomposition_ready=decomposition_ready,
    )


if __name__ == "__main__":
    main()
