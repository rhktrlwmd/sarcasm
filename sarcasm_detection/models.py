from __future__ import annotations

from sklearn.linear_model import LogisticRegression, SGDClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC


def get_candidate_models(random_state: int) -> dict[str, object]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=3000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "linear_svm": LinearSVC(
            class_weight="balanced",
            dual="auto",
            max_iter=5000,
            random_state=random_state,
        ),
        "multinomial_nb": MultinomialNB(alpha=0.5),
        "sgd_logistic": SGDClassifier(
            loss="log_loss",
            alpha=1e-4,
            max_iter=3000,
            class_weight="balanced",
            random_state=random_state,
        ),
    }
