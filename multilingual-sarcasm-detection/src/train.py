from __future__ import annotations

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from src.config import (
    DEFAULT_DECISION_THRESHOLD,
    DEFAULT_MODEL_TYPE,
    MAX_FEATURES,
    METADATA_PATH,
    MODEL_PATH,
    RANDOM_STATE,
    SUPPORTED_MODEL_TYPES,
    TEST_SIZE,
    TEST_SPLIT_PATH,
    TRAIN_SPLIT_PATH,
    VALIDATION_SIZE,
    VECTORIZER_PATH,
)
from src.data_loader import load_data, save_processed_data
from src.evaluate import calculate_metrics
from src.feature_engineering import fit_vectorizer, transform_texts
from src.preprocessing import preprocess_dataframe
from src.rules import adjust_probability_with_rules
from src.utils import bootstrap_project_directories, save_json
from src.visualization import plot_class_distribution


def build_model(model_type: str = DEFAULT_MODEL_TYPE) -> LogisticRegression:
    if model_type != "tfidf_logreg":
        raise ValueError(f"Unsupported baseline model type: {model_type}")
    return LogisticRegression(
        max_iter=2500,
        random_state=RANDOM_STATE,
        C=2.0,
        class_weight="balanced",
    )


def _select_decision_threshold(model, vectorizer, validation_df) -> float:
    if validation_df.empty:
        return DEFAULT_DECISION_THRESHOLD

    x_validation = transform_texts(vectorizer, validation_df)
    base_probabilities = model.predict_proba(x_validation)[:, 1]
    adjusted_probabilities = [
        adjust_probability_with_rules(text, probability)
        for text, probability in zip(validation_df["text"], base_probabilities)
    ]
    y_true = validation_df["label"].to_numpy()

    best_threshold = DEFAULT_DECISION_THRESHOLD
    best_accuracy = -1.0
    best_f1 = -1.0

    for step in range(35, 66):
        threshold = step / 100
        predictions = [int(probability >= threshold) for probability in adjusted_probabilities]
        metrics = calculate_metrics(y_true, predictions)
        accuracy = metrics["accuracy"]
        f1_score = metrics["f1_score"]

        if accuracy > best_accuracy or (accuracy == best_accuracy and f1_score > best_f1):
            best_threshold = threshold
            best_accuracy = accuracy
            best_f1 = f1_score

    return best_threshold


def train_model(data_paths=None, model_type: str = DEFAULT_MODEL_TYPE) -> dict:
    bootstrap_project_directories()

    raw_df = load_data(data_paths=data_paths)
    processed_df = preprocess_dataframe(raw_df)
    save_processed_data(processed_df)
    plot_class_distribution(processed_df["label"])

    stratify_labels = processed_df["label"] if processed_df["label"].nunique() > 1 else None
    train_df, test_df = train_test_split(
        processed_df,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=stratify_labels,
    )

    train_df.to_csv(TRAIN_SPLIT_PATH, index=False, encoding="utf-8")
    test_df.to_csv(TEST_SPLIT_PATH, index=False, encoding="utf-8")

    threshold_train_df, threshold_validation_df = train_test_split(
        train_df,
        test_size=VALIDATION_SIZE,
        random_state=RANDOM_STATE,
        stratify=train_df["label"] if train_df["label"].nunique() > 1 else None,
    )

    threshold_vectorizer, threshold_x_train = fit_vectorizer(threshold_train_df, max_features=MAX_FEATURES)
    threshold_model = build_model(model_type=model_type)
    threshold_model.fit(threshold_x_train, threshold_train_df["label"])
    decision_threshold = _select_decision_threshold(
        threshold_model,
        threshold_vectorizer,
        threshold_validation_df,
    )

    vectorizer, x_train = fit_vectorizer(train_df, max_features=MAX_FEATURES)
    x_test = transform_texts(vectorizer, test_df)
    y_train = train_df["label"]
    y_test = test_df["label"]

    model = build_model(model_type=model_type)
    model.fit(x_train, y_train)
    probabilities = model.predict_proba(x_test)[:, 1]
    adjusted_probabilities = [
        adjust_probability_with_rules(text, probability)
        for text, probability in zip(test_df["text"], probabilities)
    ]
    predictions = [int(probability >= decision_threshold) for probability in adjusted_probabilities]
    metrics = calculate_metrics(y_test, predictions)

    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    metadata = {
        "model_type": model_type,
        "model_description": SUPPORTED_MODEL_TYPES[model_type]["description"],
        "future_upgrade_path": SUPPORTED_MODEL_TYPES[model_type]["future_upgrade_path"],
        "feature_summary": [
            "character n-grams with case preserved",
            "word n-grams on normalized text",
            "pragmatic sarcasm signals such as CAPS, !, ?, ellipsis, and cue phrases",
        ],
        "decision_threshold": decision_threshold,
        "max_features": MAX_FEATURES,
        "test_size": TEST_SIZE,
        "validation_size": VALIDATION_SIZE,
        "random_state": RANDOM_STATE,
        "total_samples": int(len(processed_df)),
        "train_samples": int(len(train_df)),
        "test_samples": int(len(test_df)),
        "source_files": sorted(processed_df["source_file"].astype(str).unique().tolist()),
        "metrics": metrics,
    }
    save_json(metadata, METADATA_PATH)
    return metadata


def print_training_summary(training_result: dict) -> None:
    metrics = training_result["metrics"]
    print("Training completed successfully.")
    print(f"Model type: {training_result['model_type']}")
    print(f"Total samples: {training_result['total_samples']}")
    print(f"Train samples: {training_result['train_samples']}")
    print(f"Test samples : {training_result['test_samples']}")
    print(f"Source files : {len(training_result['source_files'])}")
    print(f"Threshold : {training_result['decision_threshold']:.2f}")
    print(f"Accuracy : {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall   : {metrics['recall']:.4f}")
    print(f"F1-score : {metrics['f1_score']:.4f}")


if __name__ == "__main__":
    result = train_model()
    print_training_summary(result)
