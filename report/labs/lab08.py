from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "lab08"
REPORT_IMAGE_DIR = ROOT / "report" / "image"
OUTPUT_DIR = ROOT / "outputs" / "lab08"

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.unicode_minus"] = False


def ensure_dirs() -> None:
    for path in [DATA_DIR, REPORT_IMAGE_DIR, OUTPUT_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def build_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    months = pd.date_range("2025-01-01", periods=12, freq="MS")
    regions = ["North", "South", "East", "West"]
    products = ["A", "B", "C", "D", "E"]

    anomaly_profiles = {
        ("North", "B"): {"discount_shift": 6.5, "ratio_shift": -0.18, "ratio_trend": -0.020},
        ("South", "E"): {"discount_shift": 7.0, "ratio_shift": -0.16, "ratio_trend": -0.016},
        ("West", "D"): {"discount_shift": 8.0, "ratio_shift": -0.20, "ratio_trend": -0.024},
        ("East", "C"): {"discount_shift": 3.5, "ratio_shift": -0.08, "ratio_trend": -0.010},
    }

    rows: list[dict[str, object]] = []
    for month_index, month_start in enumerate(months):
        seasonal = 1 + 0.08 * np.sin(2 * np.pi * month_index / 12)
        for region_index, region in enumerate(regions):
            for product_index, product in enumerate(products):
                base_sales = 118 + region_index * 12 + product_index * 9
                sales = base_sales * seasonal + rng.normal(0, 9)

                base_discount = 8.5 + region_index * 0.9 + product_index * 0.7
                discount = base_discount + 0.35 * month_index + rng.normal(0, 1.1)

                target_margin_pct = 0.23 + 0.008 * product_index + 0.004 * region_index
                ratio = 1.01 - 0.006 * month_index + rng.normal(0, 0.03)

                profile = anomaly_profiles.get((region, product))
                if profile is not None:
                    discount += profile["discount_shift"]
                    ratio += profile["ratio_shift"] + profile["ratio_trend"] * month_index

                margin_fact_pct = target_margin_pct * ratio
                rows.append(
                    {
                        "month": month_start.strftime("%b"),
                        "month_num": month_index + 1,
                        "region": region,
                        "product": product,
                        "sales": round(max(sales, 55), 1),
                        "target": round(max(base_sales * 0.95, 70), 1),
                        "discount_pct": round(np.clip(discount, 4, 28), 1),
                        "margin_fact_pct": round(np.clip(margin_fact_pct, 0.09, 0.33), 3),
                        "margin_target_pct": round(target_margin_pct, 3),
                    }
                )

    df = pd.DataFrame(rows)
    df["margin_ratio"] = (df["margin_fact_pct"] / df["margin_target_pct"]).round(3)
    df["is_anomaly_month"] = (df["margin_ratio"] < 0.8) & (df["discount_pct"] > 15)
    return df


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    grouped = (
        df.groupby(["region", "product"], as_index=False)
        .agg(
            avg_discount=("discount_pct", "mean"),
            avg_margin_ratio=("margin_ratio", "mean"),
            total_sales=("sales", "sum"),
            anomaly_months=("is_anomaly_month", "sum"),
        )
        .round({"avg_discount": 1, "avg_margin_ratio": 3, "total_sales": 1})
    )

    slopes = []
    declining_last_3 = []
    for row in grouped.itertuples(index=False):
        item = df[(df["region"] == row.region) & (df["product"] == row.product)].sort_values("month_num")
        slope = np.polyfit(item["month_num"], item["margin_ratio"], 1)[0]
        last_three = item["margin_ratio"].tail(3).tolist()
        slopes.append(round(float(slope), 3))
        declining_last_3.append(last_three[0] > last_three[1] > last_three[2])

    grouped["trend_slope"] = slopes
    grouped["declining_3m"] = declining_last_3
    grouped["label"] = grouped["region"] + "-" + grouped["product"]
    grouped["is_anomaly_combo"] = (grouped["avg_discount"] > 15) & (grouped["avg_margin_ratio"] < 0.8)
    grouped["severity"] = ((0.8 - grouped["avg_margin_ratio"]).clip(lower=0) * 100 + grouped["anomaly_months"]).round(2)
    grouped = grouped.sort_values(["is_anomaly_combo", "severity", "avg_discount"], ascending=[False, False, False])
    return grouped


def plot_bad_table(summary: pd.DataFrame) -> Path:
    view = summary[
        [
            "region",
            "product",
            "avg_discount",
            "avg_margin_ratio",
            "trend_slope",
            "anomaly_months",
        ]
    ].copy()
    view.columns = ["Region", "Product", "Avg discount %", "Avg margin ratio", "Trend slope", "Anomaly months"]

    fig, ax = plt.subplots(figsize=(12, 7.2))
    ax.axis("off")
    fig.suptitle(
        "Плохая версия: аналитик читает таблицу и сравнивает столбцы вручную",
        x=0.5,
        y=0.96,
        fontsize=16,
        fontweight="bold",
    )

    table = ax.table(
        cellText=view.values,
        colLabels=view.columns,
        loc="center",
        cellLoc="center",
        colLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.35)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#d7d7d7")
        if row == 0:
            cell.set_facecolor("#efefef")
            cell.set_text_props(weight="bold")
            continue

        if col == 2:
            value = float(view.iloc[row - 1, col])
            color = "#fde0c5" if value > 15 else "#f5f5f5"
        elif col == 3:
            value = float(view.iloc[row - 1, col])
            color = "#f4b4ae" if value < 0.8 else "#edf6e9"
        elif col == 4:
            value = float(view.iloc[row - 1, col])
            color = "#f8d7da" if value < 0 else "#eef2f7"
        elif col == 5:
            value = float(view.iloc[row - 1, col])
            color = "#f9c0bb" if value >= 6 else "#f7f7f7"
        else:
            color = "#ffffff"
        cell.set_facecolor(color)

    fig.text(
        0.02,
        0.045,
        "Недостаток: ответ требует последовательного чтения шести столбцов. Аномалии не выделены как единый паттерн.",
        fontsize=10,
        color="#555555",
    )

    output_path = REPORT_IMAGE_DIR / "lab08_bad_visualization.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_good_dashboard(df: pd.DataFrame, summary: pd.DataFrame) -> Path:
    anomalies = summary[summary["is_anomaly_combo"]].copy()
    watchlist = summary[~summary["is_anomaly_combo"] & summary["declining_3m"]].copy().head(2)

    fig = plt.figure(figsize=(13.5, 8.2))
    gs = fig.add_gridspec(
        nrows=4,
        ncols=4,
        width_ratios=[1.2, 1.2, 1.2, 1.0],
        height_ratios=[0.34, 1, 1, 1],
        hspace=0.38,
        wspace=0.30,
    )

    headline_ax = fig.add_subplot(gs[0, :])
    headline_ax.axis("off")
    headline = (
        f"Главный вывод: {len(anomalies)} сочетания уже находятся в красной зоне"
        " — North-B, South-E и West-D. У West-D самый сильный нисходящий тренд."
    )
    headline_ax.text(0, 0.78, headline, fontsize=16, fontweight="bold", color="#1a1a1a")
    headline_ax.text(
        0,
        0.18,
        "Красным выделены комбинации с avg margin ratio < 0.8 и avg discount > 15%. "
        "Размер точки показывает число месяцев, в которых аномалия повторялась.",
        fontsize=11,
        color="#555555",
    )

    scatter_ax = fig.add_subplot(gs[1:, :3])
    scatter_ax.set_title("Карта риска по сочетаниям регион-продукт", loc="left", fontsize=14, fontweight="bold")
    scatter_ax.axvline(15, color="#8a8a8a", linestyle="--", linewidth=1)
    scatter_ax.axhline(0.8, color="#8a8a8a", linestyle="--", linewidth=1)

    normal = summary[~summary["is_anomaly_combo"]]
    scatter_ax.scatter(
        normal["avg_discount"],
        normal["avg_margin_ratio"],
        s=40 + normal["anomaly_months"] * 22,
        color="#c8c8c8",
        alpha=0.8,
        edgecolor="none",
    )

    if not watchlist.empty:
        scatter_ax.scatter(
            watchlist["avg_discount"],
            watchlist["avg_margin_ratio"],
            s=60 + watchlist["anomaly_months"] * 22,
            color="#d8a23b",
            alpha=0.95,
            edgecolor="white",
            linewidth=0.5,
        )

    scatter_ax.scatter(
        anomalies["avg_discount"],
        anomalies["avg_margin_ratio"],
        s=80 + anomalies["anomaly_months"] * 24,
        color="#c73e1d",
        alpha=0.96,
        edgecolor="white",
        linewidth=0.6,
    )

    for row in anomalies.itertuples(index=False):
        scatter_ax.annotate(
            row.label,
            (row.avg_discount, row.avg_margin_ratio),
            xytext=(7, 7),
            textcoords="offset points",
            fontsize=10,
            color="#6a1f10",
            weight="bold",
        )

    for row in watchlist.itertuples(index=False):
        scatter_ax.annotate(
            f"{row.label} watch",
            (row.avg_discount, row.avg_margin_ratio),
            xytext=(7, -12),
            textcoords="offset points",
            fontsize=9,
            color="#7a5a10",
        )

    scatter_ax.set_xlabel("Средняя скидка, %")
    scatter_ax.set_ylabel("Маржинальность факт/цель")
    scatter_ax.set_xlim(8, 24.5)
    scatter_ax.set_ylim(0.64, 1.03)
    scatter_ax.grid(axis="y", color="#ececec", linewidth=0.8)
    scatter_ax.spines["top"].set_visible(False)
    scatter_ax.spines["right"].set_visible(False)

    trend_axes = [fig.add_subplot(gs[row, 3]) for row in [1, 2, 3]]
    anomaly_labels = anomalies["label"].tolist()
    if len(anomaly_labels) < 3:
        anomaly_labels.extend(summary.head(3 - len(anomaly_labels))["label"].tolist())

    trend_panels = anomaly_labels[:3]

    for index, (ax, label) in enumerate(zip(trend_axes, trend_panels)):
        region, product = label.split("-")
        item = df[(df["region"] == region) & (df["product"] == product)].sort_values("month_num")
        ax.plot(item["month_num"], item["margin_ratio"], color="#c73e1d", linewidth=2.2)
        ax.scatter(item["month_num"], item["margin_ratio"], color="#c73e1d", s=12, zorder=3)
        ax.axhline(0.8, color="#8a8a8a", linestyle="--", linewidth=1)
        ax.set_ylim(0.58, 1.02)
        ax.set_xlim(1, 12)
        ax.set_title(label, loc="left", fontsize=11, fontweight="bold", pad=2)
        ax.set_yticks([0.6, 0.8, 1.0])
        ax.set_xticks([1, 4, 8, 12])
        ax.set_xticklabels(["Jan", "Apr", "Aug", "Dec"], fontsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="y", color="#efefef", linewidth=0.8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        if index == 0:
            ax.text(0.0, 1.10, "Тренд по ключевым аномалиям", transform=ax.transAxes, fontsize=13, fontweight="bold")
            ax.text(0.0, 0.94, "Общая судьба: все три линии вместе идут вниз", transform=ax.transAxes, fontsize=10, color="#555555")
        ax.text(
            0.98,
            0.08,
            "3m down",
            transform=ax.transAxes,
            ha="right",
            fontsize=8,
            color="#6a1f10",
        )

    output_path = REPORT_IMAGE_DIR / "lab08_good_visualization.png"
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_path


def save_outputs(df: pd.DataFrame, summary: pd.DataFrame) -> None:
    df.to_csv(DATA_DIR / "sales_margin.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "region_product_summary.csv", index=False)

    anomalies = summary[summary["is_anomaly_combo"]][
        ["label", "avg_discount", "avg_margin_ratio", "anomaly_months", "trend_slope"]
    ].copy()
    anomalies.to_csv(OUTPUT_DIR / "anomalies.csv", index=False)


def main() -> None:
    ensure_dirs()
    df = build_dataset()
    summary = build_summary(df)
    save_outputs(df, summary)
    plot_bad_table(summary)
    plot_good_dashboard(df, summary)
    print("Saved dataset to", DATA_DIR / "sales_margin.csv")
    print("Saved plots to", REPORT_IMAGE_DIR)


if __name__ == "__main__":
    main()
