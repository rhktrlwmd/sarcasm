from __future__ import annotations

import warnings

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.exceptions import ConvergenceWarning
from sklearn.svm import LinearSVC

from src.config import (
    MAX_FEATURES,
    MODEL_COMPARISON_MARKDOWN_PATH,
    MODEL_COMPARISON_PATH,
    RANDOM_STATE,
    TEST_SIZE,
)
from src.data_loader import load_data
from src.feature_engineering import fit_vectorizer, transform_texts
from src.preprocessing import preprocess_dataframe
from src.utils import bootstrap_project_directories
from src.visualization import plot_model_comparison


def _dataframe_to_markdown(results_df: pd.DataFrame) -> str:
    headers = list(results_df.columns)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in results_df.itertuples(index=False):
        formatted = [
            f"{value:.4f}" if isinstance(value, float) else str(value)
            for value in row
        ]
        lines.append("| " + " | ".join(formatted) + " |")
    return "\n".join(lines)


def _build_comparison_models() -> list[tuple[str, object]]:
    return [
        (
            "Logistic Regression",
            LogisticRegression(
                max_iter=2500,
                random_state=RANDOM_STATE,
                C=2.0,
                class_weight="balanced",
            ),
        ),
        ("Naive Bayes", MultinomialNB(alpha=0.5)),
        (
            "Linear SVM",
            LinearSVC(
                C=0.8,
                class_weight="balanced",
                random_state=RANDOM_STATE,
                dual="auto",
                max_iter=100000,
                tol=1e-3,
            ),
        ),
    ]


def compare_models(data_paths=None) -> dict:
    bootstrap_project_directories()

    raw_df = load_data(data_paths=data_paths)
    processed_df = preprocess_dataframe(raw_df)
    train_df, test_df = train_test_split(
        processed_df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=processed_df["label"] if processed_df["label"].nunique() > 1 else None,
    )

    vectorizer, x_train = fit_vectorizer(train_df, max_features=MAX_FEATURES)
    x_test = transform_texts(vectorizer, test_df)
    y_train = train_df["label"]
    y_test = test_df["label"]

    results: list[dict] = []
    for model_name, model in _build_comparison_models():
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning)
            model.fit(x_train, y_train)
        predictions = model.predict(x_test)
        results.append(
            {
                "Model": model_name,
                "Accuracy": accuracy_score(y_test, predictions),
                "F1": f1_score(y_test, predictions, zero_division=0),
                "Precision": precision_score(y_test, predictions, zero_division=0),
                "Recall": recall_score(y_test, predictions, zero_division=0),
            }
        )

    results_df = pd.DataFrame(results).sort_values(by=["Accuracy", "F1"], ascending=False).reset_index(drop=True)
    MODEL_COMPARISON_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(MODEL_COMPARISON_PATH, index=False, encoding="utf-8")

    markdown_table = _dataframe_to_markdown(results_df)
    MODEL_COMPARISON_MARKDOWN_PATH.write_text(markdown_table + "\n", encoding="utf-8")
    plot_path = plot_model_comparison(results_df)

    return {
        "results": results_df,
        "csv_path": str(MODEL_COMPARISON_PATH),
        "markdown_path": str(MODEL_COMPARISON_MARKDOWN_PATH),
        "plot_path": str(plot_path),
        "train_samples": int(len(train_df)),
        "test_samples": int(len(test_df)),
    }


if __name__ == "__main__":
    comparison = compare_models()
    print(comparison["results"].to_string(index=False, float_format=lambda value: f"{value:.4f}"))
