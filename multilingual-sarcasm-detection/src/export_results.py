from __future__ import annotations

import shutil
from pathlib import Path

from src.compare_models import compare_models
from src.config import (
    CLASSIFICATION_REPORT_PATH,
    CONFUSION_MATRIX_RESULTS_PATH,
    MODEL_COMPARISON_MARKDOWN_PATH,
    MODEL_COMPARISON_PATH,
    MODEL_COMPARISON_PLOT,
    RESULTS_PATH,
)
from src.evaluate import evaluate_model
from src.prepare_real_datasets import prepare_real_datasets
from src.utils import bootstrap_project_directories


def _copy_file(source_path: Path, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination_path)


def export_results() -> dict:
    bootstrap_project_directories()

    data_paths = prepare_real_datasets(include_manual_russian_conversational=True)
    compare_models(data_paths=data_paths)
    evaluation = evaluate_model()

    _copy_file(MODEL_COMPARISON_PATH, RESULTS_PATH / MODEL_COMPARISON_PATH.name)
    _copy_file(MODEL_COMPARISON_MARKDOWN_PATH, RESULTS_PATH / MODEL_COMPARISON_MARKDOWN_PATH.name)
    _copy_file(MODEL_COMPARISON_PLOT, RESULTS_PATH / MODEL_COMPARISON_PLOT.name)
    _copy_file(Path(evaluation["confusion_matrix_plot"]), CONFUSION_MATRIX_RESULTS_PATH)

    report_lines = [
        "Sarcasm Detection Evaluation Report",
        "",
        f"Decision threshold: {evaluation['decision_threshold']:.2f}",
        "",
        "Classification report:",
        evaluation["classification_report"].rstrip(),
        "",
        "Metrics:",
        f"Accuracy : {evaluation['metrics']['accuracy']:.4f}",
        f"Precision: {evaluation['metrics']['precision']:.4f}",
        f"Recall   : {evaluation['metrics']['recall']:.4f}",
        f"F1-score : {evaluation['metrics']['f1_score']:.4f}",
    ]
    CLASSIFICATION_REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return {
        "results_path": str(RESULTS_PATH),
        "classification_report_path": str(CLASSIFICATION_REPORT_PATH),
        "confusion_matrix_path": str(CONFUSION_MATRIX_RESULTS_PATH),
        "model_comparison_csv_path": str(RESULTS_PATH / MODEL_COMPARISON_PATH.name),
        "model_comparison_markdown_path": str(RESULTS_PATH / MODEL_COMPARISON_MARKDOWN_PATH.name),
        "model_comparison_plot_path": str(RESULTS_PATH / MODEL_COMPARISON_PLOT.name),
    }


if __name__ == "__main__":
    result = export_results()
    for key, value in result.items():
        print(f"{key}: {value}")
