from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support

from src.config import DEFAULT_DECISION_THRESHOLD, METADATA_PATH, MODEL_PATH, TEST_SPLIT_PATH, VECTORIZER_PATH
from src.feature_engineering import transform_texts
from src.rules import adjust_probability_with_rules
from src.utils import load_json
from src.visualization import plot_confusion_matrix


def calculate_metrics(y_true, y_pred) -> dict:
    precision, recall, f1_score, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        average="binary",
        zero_division=0,
    )
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
    }


def evaluate_model(
    test_data_path: Path = TEST_SPLIT_PATH,
    model_path: Path = MODEL_PATH,
    vectorizer_path: Path = VECTORIZER_PATH,
) -> dict:
    if not test_data_path.exists():
        raise FileNotFoundError(f"Test split not found: {test_data_path}. Train the model first.")

    test_df = pd.read_csv(test_data_path)
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)
    metadata = load_json(METADATA_PATH)
    decision_threshold = float(metadata.get("decision_threshold", DEFAULT_DECISION_THRESHOLD))

    x_test = transform_texts(vectorizer, test_df)
    y_true = test_df["label"]
    base_probabilities = model.predict_proba(x_test)[:, 1]
    adjusted_probabilities = [
        adjust_probability_with_rules(text, probability)
        for text, probability in zip(test_df["text"], base_probabilities)
    ]
    y_pred = [int(probability >= decision_threshold) for probability in adjusted_probabilities]

    metrics = calculate_metrics(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=["Not Sarcastic", "Sarcastic"], zero_division=0)
    matrix = confusion_matrix(y_true, y_pred)
    confusion_plot = plot_confusion_matrix(matrix)

    return {
        "metrics": metrics,
        "decision_threshold": decision_threshold,
        "classification_report": report,
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_plot": str(confusion_plot),
    }
