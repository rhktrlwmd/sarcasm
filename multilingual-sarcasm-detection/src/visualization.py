from __future__ import annotations

import os
from pathlib import Path

from src.config import (
    CLASS_DISTRIBUTION_PLOT,
    CONFUSION_MATRIX_PLOT,
    MODEL_COMPARISON_PLOT,
    PREDICTION_PROBABILITY_PLOT,
    PROCESSED_DATA_PATH,
)

os.environ.setdefault("MPLCONFIGDIR", str(PROCESSED_DATA_PATH / ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import ConfusionMatrixDisplay

sns.set_theme(style="whitegrid")


def plot_class_distribution(labels, output_path: Path = CLASS_DISTRIBUTION_PLOT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(6, 4))
    sns.countplot(x=list(labels), hue=list(labels), palette="viridis", legend=False)
    plt.title("Class Distribution")
    plt.xlabel("Label")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()
    return output_path


def plot_confusion_matrix(confusion_matrix, output_path: Path = CONFUSION_MATRIX_PLOT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 5))
    display = ConfusionMatrixDisplay(confusion_matrix=confusion_matrix, display_labels=["Not Sarcastic", "Sarcastic"])
    display.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Confusion Matrix")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_prediction_probability(probability: float, output_path: Path = PREDICTION_PROBABILITY_PLOT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    probability = float(probability)
    fig, ax = plt.subplots(figsize=(7, 2.2))
    ax.barh(["Sarcasm probability"], [probability], color="#d95f02")
    ax.set_xlim(0, 1)
    ax.set_xlabel("Probability")
    ax.set_title("Prediction Probability")
    ax.text(min(probability + 0.02, 0.96), 0, f"{probability:.2%}", va="center")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_model_comparison(results_df, output_path: Path = MODEL_COMPARISON_PLOT) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    melted_df = results_df.melt(
        id_vars="Model",
        value_vars=["Accuracy", "F1"],
        var_name="Metric",
        value_name="Score",
    )
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(data=melted_df, x="Model", y="Score", hue="Metric", palette="crest", ax=ax)
    ax.set_ylim(0, 1)
    ax.set_title("Model Comparison")
    ax.set_ylabel("Score")
    ax.set_xlabel("")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path
