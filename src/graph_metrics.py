from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TimeWindow:
    window_id: int
    time_start: pd.Timestamp
    time_end: pd.Timestamp
    chunk: pd.DataFrame

    @property
    def time_center(self) -> pd.Timestamp:
        return self.time_start + (self.time_end - self.time_start) / 2


def split_into_event_windows(df: pd.DataFrame, window_size: int) -> list[TimeWindow]:
    if df.empty:
        return []
    windows: list[TimeWindow] = []
    working = df.sort_values("timestamp").reset_index(drop=True)
    if window_size <= 0:
        raise ValueError("window_size must be positive")

    for start_index in range(0, len(working), window_size):
        chunk = working.iloc[start_index : start_index + window_size].copy()
        if chunk.empty:
            continue
        windows.append(
            TimeWindow(
                window_id=(start_index // window_size) + 1,
                time_start=pd.to_datetime(chunk["timestamp"].min()),
                time_end=pd.to_datetime(chunk["timestamp"].max()),
                chunk=chunk,
            )
        )
    return windows


def build_graph(chunk: pd.DataFrame, directed: bool = False) -> nx.Graph | nx.DiGraph:
    graph = nx.DiGraph() if directed else nx.Graph()
    if not chunk.empty:
        edges = chunk[["source", "target"]].itertuples(index=False, name=None)
        graph.add_edges_from(edges)
    return graph


def _connected_components_count(graph: nx.Graph | nx.DiGraph) -> int:
    if len(graph) == 0:
        return 0
    if graph.is_directed():
        return nx.number_weakly_connected_components(graph)
    return nx.number_connected_components(graph)


def _is_connected(graph: nx.Graph | nx.DiGraph) -> bool:
    if len(graph) == 0:
        return False
    if graph.is_directed():
        return nx.is_weakly_connected(graph)
    return nx.is_connected(graph)


def _diameter(graph: nx.Graph | nx.DiGraph) -> float:
    if len(graph) == 1:
        return 0.0
    if not _is_connected(graph):
        return np.nan
    base_graph = graph.to_undirected() if graph.is_directed() else graph
    return float(nx.diameter(base_graph))


def _avg_clustering(graph: nx.Graph | nx.DiGraph) -> float:
    if len(graph) <= 1:
        return 0.0
    base_graph = graph.to_undirected() if graph.is_directed() else graph
    return float(nx.average_clustering(base_graph))


def compute_window_metrics(
    window: TimeWindow,
    directed: bool = False,
) -> tuple[dict[str, float | int | str | pd.Timestamp], dict[str, float]]:
    graph = build_graph(window.chunk, directed=directed)
    degrees = [degree for _, degree in graph.degree()]
    avg_degree = float(np.mean(degrees)) if degrees else 0.0
    density = float(nx.density(graph)) if len(graph) > 1 else 0.0
    avg_clustering = _avg_clustering(graph)
    n_components = _connected_components_count(graph)
    diameter = _diameter(graph)

    betweenness = nx.betweenness_centrality(graph) if len(graph) > 0 else {}
    bet_values = list(betweenness.values())
    betweenness_mean = float(np.mean(bet_values)) if bet_values else 0.0
    betweenness_max = float(np.max(bet_values)) if bet_values else 0.0

    metrics: dict[str, float | int | str | pd.Timestamp] = {
        "window_id": window.window_id,
        "time_start": window.time_start,
        "time_end": window.time_end,
        "time_center": window.time_center,
        "n_events": int(len(window.chunk)),
        "n_nodes": int(graph.number_of_nodes()),
        "n_edges": int(graph.number_of_edges()),
        "avg_degree": avg_degree,
        "density": density,
        "avg_clustering": avg_clustering,
        "n_components": n_components,
        "diameter": diameter,
        "betweenness_mean": betweenness_mean,
        "betweenness_max": betweenness_max,
    }

    if directed:
        in_degrees = dict(graph.in_degree())
        out_degrees = dict(graph.out_degree())
        ratios: list[float] = []
        for node in graph.nodes():
            out_value = out_degrees[node]
            in_value = in_degrees[node]
            ratios.append(in_value / out_value if out_value != 0 else np.nan)
        metrics["in_out_ratio_mean"] = float(np.nanmean(ratios)) if ratios else np.nan

    return metrics, betweenness


def compute_metrics_table(
    df: pd.DataFrame,
    window_size: int,
    directed: bool = False,
    all_nodes: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    nodes = all_nodes or sorted(set(df["source"]).union(set(df["target"])))
    metric_rows: list[dict[str, float | int | str | pd.Timestamp]] = []
    betweenness_rows: list[dict[str, float | int | str | pd.Timestamp]] = []

    for window in split_into_event_windows(df, window_size):
        metrics, node_betweenness = compute_window_metrics(window, directed=directed)
        metric_rows.append(metrics)

        for node in nodes:
            betweenness_rows.append(
                {
                    "window_id": window.window_id,
                    "time_start": window.time_start,
                    "time_end": window.time_end,
                    "time_center": window.time_center,
                    "node": node,
                    "betweenness": float(node_betweenness.get(node, 0.0)),
                }
            )

    return pd.DataFrame(metric_rows), pd.DataFrame(betweenness_rows)
