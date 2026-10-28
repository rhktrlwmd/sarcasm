from __future__ import annotations

from pathlib import Path
from typing import Iterable

import joblib
import pandas as pd

from src.config import DEFAULT_DECISION_THRESHOLD, METADATA_PATH, MODEL_PATH, UNCERTAIN_MARGIN, VECTORIZER_PATH
from src.feature_engineering import transform_texts
from src.preprocessing import clean_text, prepare_text_for_model
from src.rules import adjust_probability_with_rules, sarcasm_rule_score
from src.utils import load_json
from src.visualization import plot_prediction_probability


def _load_artifacts(model_path: Path = MODEL_PATH, vectorizer_path: Path = VECTORIZER_PATH):
    if not model_path.exists() or not vectorizer_path.exists():
        raise FileNotFoundError("Model artifacts are missing. Train the model first.")
    return joblib.load(model_path), joblib.load(vectorizer_path)


def _load_decision_threshold() -> float:
    metadata = load_json(METADATA_PATH)
    return float(metadata.get("decision_threshold", DEFAULT_DECISION_THRESHOLD))


def _prediction_label_from_probability(probability: float, decision_threshold: float) -> str:
    low = max(0.0, decision_threshold - UNCERTAIN_MARGIN)
    high = min(1.0, decision_threshold + UNCERTAIN_MARGIN)
    if low <= probability <= high:
        return "Uncertain"
    return "Sarcastic" if probability > decision_threshold else "NotSarcastic"


def predict_text(text: str, model_path: Path = MODEL_PATH, vectorizer_path: Path = VECTORIZER_PATH) -> dict:
    model, vectorizer = _load_artifacts(model_path, vectorizer_path)
    decision_threshold = _load_decision_threshold()
    model_text = prepare_text_for_model(text)
    cleaned_text = clean_text(text)
    feature_df = pd.DataFrame(
        [{"text": text, "model_text": model_text, "clean_text": cleaned_text}]
    )
    features = transform_texts(vectorizer, feature_df)
    base_probability = float(model.predict_proba(features)[0][1])
    probability = adjust_probability_with_rules(text, base_probability)
    predicted_label = int(probability >= decision_threshold)
    prediction_label = _prediction_label_from_probability(probability, decision_threshold)
    plot_path = plot_prediction_probability(probability)
    return {
        "text": text,
        "model_text": model_text,
        "clean_text": cleaned_text,
        "label": predicted_label,
        "prediction": prediction_label,
        "binary_prediction": "Sarcastic" if predicted_label == 1 else "NotSarcastic",
        "probability": probability,
        "base_probability": base_probability,
        "decision_threshold": decision_threshold,
        "rule_score": sarcasm_rule_score(text),
        "probability_plot": str(plot_path),
        "is_uncertain": prediction_label == "Uncertain",
    }


def predict_batch(
    texts: Iterable[str] | pd.DataFrame,
    model_path: Path = MODEL_PATH,
    vectorizer_path: Path = VECTORIZER_PATH,
) -> pd.DataFrame:
    model, vectorizer = _load_artifacts(model_path, vectorizer_path)
    decision_threshold = _load_decision_threshold()

    if isinstance(texts, pd.DataFrame):
        if "text" not in texts.columns:
            raise ValueError("Batch DataFrame must contain a 'text' column.")
        batch_df = texts.copy()
    else:
        batch_df = pd.DataFrame({"text": list(texts)})

    batch_df["model_text"] = batch_df["text"].apply(prepare_text_for_model)
    batch_df["clean_text"] = batch_df["text"].apply(clean_text)
    features = transform_texts(vectorizer, batch_df)
    batch_df["base_probability"] = model.predict_proba(features)[:, 1]
    batch_df["rule_score"] = batch_df["text"].apply(sarcasm_rule_score)
    batch_df["sarcasm_probability"] = [
        adjust_probability_with_rules(text, probability)
        for text, probability in zip(batch_df["text"], batch_df["base_probability"])
    ]
    batch_df["predicted_label"] = (batch_df["sarcasm_probability"] >= decision_threshold).astype(int)
    batch_df["prediction"] = batch_df["sarcasm_probability"].apply(
        lambda probability: _prediction_label_from_probability(probability, decision_threshold)
    )
    batch_df["binary_prediction"] = batch_df["predicted_label"].map({0: "NotSarcastic", 1: "Sarcastic"})
    batch_df["is_uncertain"] = batch_df["prediction"].eq("Uncertain")
    batch_df["decision_threshold"] = decision_threshold
    return batch_df
