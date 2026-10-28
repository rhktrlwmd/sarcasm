from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed"
RESULTS_PATH = PROJECT_ROOT / "results"
MODEL_PATH = PROJECT_ROOT / "models" / "sarcasm_model.pkl"
VECTORIZER_PATH = PROJECT_ROOT / "models" / "tfidf_vectorizer.pkl"
METADATA_PATH = PROJECT_ROOT / "models" / "model_metadata.json"
PROCESSED_DATASET_PATH = PROCESSED_DATA_PATH / "combined_dataset.csv"
TRAIN_SPLIT_PATH = PROCESSED_DATA_PATH / "train_split.csv"
TEST_SPLIT_PATH = PROCESSED_DATA_PATH / "test_split.csv"
CLASS_DISTRIBUTION_PLOT = PROCESSED_DATA_PATH / "plots" / "class_distribution.png"
CONFUSION_MATRIX_PLOT = PROCESSED_DATA_PATH / "plots" / "confusion_matrix.png"
PREDICTION_PROBABILITY_PLOT = PROCESSED_DATA_PATH / "plots" / "prediction_probability.png"
MODEL_COMPARISON_PATH = PROCESSED_DATA_PATH / "model_comparison.csv"
MODEL_COMPARISON_MARKDOWN_PATH = PROCESSED_DATA_PATH / "model_comparison.md"
MODEL_COMPARISON_PLOT = PROCESSED_DATA_PATH / "plots" / "model_comparison.png"
CLASSIFICATION_REPORT_PATH = RESULTS_PATH / "classification_report.txt"
CONFUSION_MATRIX_RESULTS_PATH = RESULTS_PATH / "confusion_matrix.png"

TEST_SIZE = 0.2
VALIDATION_SIZE = 0.15
RANDOM_STATE = 42
MAX_FEATURES = 20000
DEFAULT_DECISION_THRESHOLD = 0.5
UNCERTAIN_MARGIN = 0.05

DEFAULT_MODEL_TYPE = "tfidf_logreg"
SUPPORTED_MODEL_TYPES = {
    "tfidf_logreg": {
        "description": "Case-aware character and word TF-IDF + tuned Logistic Regression baseline",
        "future_upgrade_path": ["mBERT", "XLM-RoBERTa", "DistilBERT"],
    }
}
