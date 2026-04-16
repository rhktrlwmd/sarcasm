from __future__ import annotations

import re

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F900-\U0001F9FF"
    "]+",
    flags=re.UNICODE,
)
WORD_PATTERN = re.compile(r"[A-Za-z']+")

POSITIVE_WORDS = {
    "amazing",
    "awesome",
    "brilliant",
    "fantastic",
    "great",
    "love",
    "perfect",
    "wonderful",
}
NEGATIVE_WORDS = {
    "awful",
    "bad",
    "boring",
    "hate",
    "terrible",
    "worse",
    "worst",
    "useless",
}
CONTRAST_MARKERS = {
    "yeah_right",
    "as_if",
    "sure",
    "totally",
    "obviously",
    "clearly",
    "thanks_for_nothing",
}
INTENSIFIERS = {"absolutely", "completely", "extremely", "literally", "really", "so", "totally"}
NEGATIONS = {"never", "no", "not", "nothing", "n't"}
LAUGHTER = {"haha", "hehe", "lol", "lmao", "rofl"}


class PragmaticFeatureExtractor(BaseEstimator, TransformerMixin):
    feature_names_ = (
        "char_count",
        "token_count",
        "avg_token_length",
        "exclamation_count",
        "question_count",
        "ellipsis_count",
        "quote_count",
        "uppercase_ratio",
        "emoji_count",
        "positive_word_count",
        "negative_word_count",
        "contrast_marker_count",
        "intensifier_count",
        "negation_count",
        "laughter_count",
    )

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        rows = [self._extract_features(str(text)) for text in X]
        return csr_matrix(np.asarray(rows, dtype=float))

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_, dtype=object)

    def _extract_features(self, text: str) -> list[float]:
        tokens = WORD_PATTERN.findall(text)
        lowered_tokens = [token.lower() for token in tokens]
        char_count = float(len(text))
        token_count = float(len(tokens))
        avg_token_length = float(np.mean([len(token) for token in tokens])) if tokens else 0.0
        exclamation_count = float(text.count("!"))
        question_count = float(text.count("?"))
        ellipsis_count = float(text.count("..."))
        quote_count = float(text.count('"') + text.count("'"))
        uppercase_words = [token for token in tokens if len(token) > 1 and token.isupper()]
        uppercase_ratio = float(len(uppercase_words) / len(tokens)) if tokens else 0.0
        emoji_count = float(len(EMOJI_PATTERN.findall(text)))

        contrast_text = text.lower().replace("yeah right", "yeah_right").replace("as if", "as_if")
        contrast_text = contrast_text.replace("thanks for nothing", "thanks_for_nothing")
        contrast_words = set(WORD_PATTERN.findall(contrast_text))

        return [
            char_count,
            token_count,
            avg_token_length,
            exclamation_count,
            question_count,
            ellipsis_count,
            quote_count,
            uppercase_ratio,
            emoji_count,
            float(sum(token in POSITIVE_WORDS for token in lowered_tokens)),
            float(sum(token in NEGATIVE_WORDS for token in lowered_tokens)),
            float(sum(token in CONTRAST_MARKERS for token in contrast_words)),
            float(sum(token in INTENSIFIERS for token in lowered_tokens)),
            float(sum(token in NEGATIONS for token in lowered_tokens)),
            float(sum(token in LAUGHTER for token in lowered_tokens)),
        ]


def build_feature_extractor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "word_tfidf",
                TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, sublinear_tf=True),
                "clean_text",
            ),
            (
                "char_tfidf",
                TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1, sublinear_tf=True),
                "clean_text",
            ),
            ("pragmatic", PragmaticFeatureExtractor(), "text"),
            ("platform", OneHotEncoder(handle_unknown="ignore"), ["platform"]),
        ],
        remainder="drop",
    )

