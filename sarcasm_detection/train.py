from __future__ import annotations

import argparse
import json
import os
import pickle
import warnings
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("KMP_USE_SHM", "0")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline

from .config import SarcasmProjectConfig
from .data import build_stratify_labels, load_all_datasets, save_dataset_summary
from .features import build_feature_extractor
from .models import get_candidate_models
from .preprocessing import SocialTextPreprocessor

warnings.filterwarnings("ignore", category=FutureWarning, module=r"sklearn\.svm")
warnings.filterwarnings("ignore", category=ConvergenceWarning, module=r"sklearn\.svm")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train sarcasm detection models on social media datasets.")
    parser.add_argument("--dataset-dir", type=Path, default=None, help="Directory with CSV datasets.")
    parser.add_argument("--disable-lemmatization", action="store_true", help="Turn off lemmatization.")
    parser.add_argument("--enable-stemming", action="store_true", help="Turn on stemming.")
    return parser.parse_args()


def add_clean_text(dataset: pd.DataFrame, preprocessor: SocialTextPreprocessor) -> pd.DataFrame:
    working = dataset.copy()
    working["clean_text"] = preprocessor.transform(working["text"].astype(str).tolist())
    return working


def compute_auc(model: Pipeline, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    try:
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(X_test)[:, 1]
            return float(roc_auc_score(y_test, probabilities))
        if hasattr(model, "decision_function"):
            scores = model.decision_function(X_test)
            return float(roc_auc_score(y_test, scores))
    except Exception:
        return float("nan")
    return float("nan")


def save_confusion_matrix(y_true: pd.Series, y_pred: np.ndarray, output_path: Path, title: str) -> None:
    figure, axis = plt.subplots(figsize=(5, 4))
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, ax=axis, cmap="Blues", colorbar=False)
    axis.set_title(title)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def save_linear_feature_importance(model: Pipeline, output_path: Path, top_k: int = 20) -> None:
    classifier = model.named_steps["classifier"]
    if not hasattr(classifier, "coef_"):
        return

    feature_extractor = model.named_steps["features"]
    feature_names = feature_extractor.get_feature_names_out()
    coefficients = classifier.coef_[0]
    ranking = pd.DataFrame({"feature": feature_names, "weight": coefficients})
    top_positive = ranking.sort_values("weight", ascending=False).head(top_k)
    top_negative = ranking.sort_values("weight", ascending=True).head(top_k)

    report = pd.concat(
        [
            top_positive.assign(direction="sarcastic"),
            top_negative.assign(direction="non_sarcastic"),
        ],
        ignore_index=True,
    )
    report.to_csv(output_path, index=False)


def evaluate_per_platform(y_true: pd.Series, y_pred: np.ndarray, platforms: pd.Series) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for platform in sorted(platforms.unique()):
        mask = platforms == platform
        rows.append(
            {
                "platform": platform,
                "samples": int(mask.sum()),
                "accuracy": float(accuracy_score(y_true[mask], y_pred[mask])),
                "precision": float(precision_score(y_true[mask], y_pred[mask], zero_division=0)),
                "recall": float(recall_score(y_true[mask], y_pred[mask], zero_division=0)),
                "f1": float(f1_score(y_true[mask], y_pred[mask], zero_division=0)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    config = SarcasmProjectConfig()
    config.ensure_directories()

    config.preprocessing.apply_lemmatization = not args.disable_lemmatization
    config.preprocessing.apply_stemming = args.enable_stemming

    dataset, source_files = load_all_datasets(config, dataset_dir=args.dataset_dir)
    preprocessor = SocialTextPreprocessor(config.preprocessing)
    dataset = add_clean_text(dataset, preprocessor)

    dataset.to_csv(config.processed_data_dir / "combined_dataset.csv", index=False)
    save_dataset_summary(dataset, config.processed_data_dir / "dataset_summary.csv")

    stratify_labels = build_stratify_labels(dataset)
    X_train, X_test, y_train, y_test = train_test_split(
        dataset[["text", "clean_text", "platform"]],
        dataset["label"],
        test_size=config.training.test_size,
        random_state=config.training.random_state,
        stratify=stratify_labels,
    )

    cv = StratifiedKFold(
        n_splits=config.training.cv_folds,
        shuffle=True,
        random_state=config.training.random_state,
    )
    candidate_models = get_candidate_models(config.training.random_state)

    results: list[dict[str, object]] = []
    trained_models: dict[str, Pipeline] = {}

    for model_name, estimator in candidate_models.items():
        pipeline = Pipeline(
            steps=[
                ("features", build_feature_extractor()),
                ("classifier", estimator),
            ]
        )

        cv_scores = cross_val_score(clone(pipeline), X_train, y_train, cv=cv, scoring="f1")
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        trained_models[model_name] = pipeline

        report_dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        per_platform = evaluate_per_platform(y_test.reset_index(drop=True), y_pred, X_test["platform"].reset_index(drop=True))
        per_platform.to_csv(config.outputs_dir / f"{model_name}_per_platform_metrics.csv", index=False)
        save_confusion_matrix(
            y_test,
            y_pred,
            config.figures_dir / f"{model_name}_confusion_matrix.png",
            title=f"{model_name} confusion matrix",
        )

        result = {
            "model": model_name,
            "cv_f1_mean": float(np.mean(cv_scores)),
            "cv_f1_std": float(np.std(cv_scores)),
            "test_accuracy": float(accuracy_score(y_test, y_pred)),
            "test_precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "test_recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "test_f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "test_roc_auc": compute_auc(pipeline, X_test, y_test),
            "support_sarcastic": int(report_dict["1"]["support"]),
            "support_non_sarcastic": int(report_dict["0"]["support"]),
        }
        results.append(result)

        with (config.outputs_dir / f"{model_name}_classification_report.json").open("w", encoding="utf-8") as handle:
            json.dump(report_dict, handle, ensure_ascii=False, indent=2)

    results_df = pd.DataFrame(results).sort_values("test_f1", ascending=False).reset_index(drop=True)
    results_df.to_csv(config.outputs_dir / "model_comparison.csv", index=False)

    best_model_name = str(results_df.iloc[0]["model"])
    best_model = trained_models[best_model_name]
    best_predictions = best_model.predict(X_test)

    test_predictions = X_test.copy()
    test_predictions["true_label"] = y_test.to_numpy()
    test_predictions["predicted_label"] = best_predictions
    test_predictions["error"] = (test_predictions["true_label"] != test_predictions["predicted_label"]).astype(int)
    test_predictions.to_csv(config.outputs_dir / "test_predictions.csv", index=False)

    save_linear_feature_importance(best_model, config.outputs_dir / f"{best_model_name}_top_features.csv")

    model_bundle = {
        "model_name": best_model_name,
        "pipeline": best_model,
        "preprocessor": preprocessor,
        "preprocessing_config": preprocessor.get_config_dict(),
        "source_files": [path.name for path in source_files],
        "results": results,
    }
    with (config.models_dir / "best_model.pkl").open("wb") as handle:
        pickle.dump(model_bundle, handle)

    summary = [
        "Sarcasm detection diploma project",
        f"Samples: {len(dataset)}",
        f"Platforms: {', '.join(sorted(dataset['platform'].unique()))}",
        f"Best model: {best_model_name}",
        f"Best test F1: {results_df.iloc[0]['test_f1']:.4f}",
        f"Lemmatization enabled: {config.preprocessing.apply_lemmatization}",
        f"Stemming enabled: {config.preprocessing.apply_stemming}",
    ]
    (config.outputs_dir / "training_summary.txt").write_text("\n".join(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
