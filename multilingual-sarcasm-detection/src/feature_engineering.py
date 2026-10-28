from __future__ import annotations

import re

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import MAX_FEATURES
from src.preprocessing import clean_text, prepare_text_for_model

TOKEN_PATTERN = re.compile(r"\b\w+\b", flags=re.UNICODE)
REPEATED_PUNCTUATION_PATTERN = re.compile(r"([!?])\1+", flags=re.UNICODE)
ELONGATED_PATTERN = re.compile(r"(.)\1{2,}", flags=re.IGNORECASE | re.UNICODE)
POSITIVE_CUE_WORDS = [
    "great",
    "amazing",
    "wonderful",
    "fantastic",
    "perfect",
    "perfecto",
    "brilliant",
    "awesome",
    "lovely",
    "helpful",
    "love",
    "dream",
    "excellent",
    "nice",
    "cool",
    "smart",
    "intelligent",
    "brilliant",
    "clever",
    "genius",
    "вау",
    "отлично",
    "прекрасно",
    "великолепно",
    "супер",
    "замечательно",
    "счастье",
    "вовремя",
    "обожаю",
    "круто",
    "умная",
    "умный",
    "гений",
    "интеллектуал",
]
NEGATIVE_EVENT_WORDS = [
    "crashed",
    "crash",
    "deadline",
    "traffic",
    "homework",
    "meeting",
    "broken",
    "stopped",
    "late",
    "jam",
    "stuck",
    "rain",
    "pouring",
    "bug",
    "error",
    "failed",
    "fails",
    "elevator",
    "laptop",
    "phone",
    "battery",
    "problem",
    "problems",
    "urgent",
    "cancelled",
    "canceled",
    "disappeared",
    "waking",
    "5 a m",
    "5am",
    "exam",
    "wifi",
    "wi fi",
    "reply",
    "weeks",
    "late",
    "слом",
    "баг",
    "дедлайн",
    "сюрприз",
    "пропал",
    "созвон",
    "ответил",
    "недели",
    "месяц",
    "лифт",
    "компьютер",
    "телефон",
    "разряд",
    "сломал",
    "не работает",
    "момент",
    "проблем",
    "ошиб",
    "срочн",
    "отключ",
]
CONTRAST_PATTERNS = [
    "what a wonderful",
    "what a surprise",
    "because waking up",
    "everyone s dream",
    "i really needed another",
    "please take your time",
    "nothing else to do",
    "right before the deadline",
    "stuck in traffic",
    "pouring rain",
    "broken again",
    "stopped working",
    "reply to my email",
    "через три недели",
    "мне вообще нечего делать",
    "как же я люблю",
    "опять",
    "какое счастье",
    "снова не работает",
    "в самый нужный момент",
    "опять сломался",
    "ты такая умная",
    "ты такой умный",
    "так интересно",
    "так рада",
    "так рад",
    "youre so smart",
    "you are so smart",
    "youre so intelligent",
    "you are so intelligent",
    "youre so brilliant",
    "you are so brilliant",
    "so interesting",
    "so happy",
    "so glad",
]
SARCASM_HINTS = [
    "yeah right",
    "as if",
    "sure",
    "totally",
    "please take your time",
    "nothing else to do",
    "of course",
    "brilliant",
    "great",
    "amazing",
    "didnt know about that",
    "didn't know about that",
    "didnt see that coming",
    "didn't see that coming",
    "eat my shoes",
    "ну да",
    "ага",
    "конечно",
    "ну конечно",
    "как же",
    "очень вовремя",
    "спасибо",
    "отлично",
    "прекрасно",
    "великолепно",
    "замечательно",
    "какое счастье",
    "вау",
    "perfecto",
    "claro",
    "formidable",
    "wunderbar",
    "fantastico",
]


def create_char_vectorizer(max_features: int = MAX_FEATURES) -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 5),
        max_features=max_features,
        lowercase=False,
    )


def create_word_vectorizer(max_features: int = MAX_FEATURES // 2) -> TfidfVectorizer:
    return TfidfVectorizer(
        analyzer="word",
        ngram_range=(1, 2),
        max_features=max_features,
        lowercase=False,
        token_pattern=r"(?u)\b\w+\b",
    )


def _ensure_feature_frame(texts) -> pd.DataFrame:
    if isinstance(texts, pd.DataFrame):
        feature_df = texts.copy()
        if "text" not in feature_df.columns:
            raise ValueError("Input DataFrame must contain a 'text' column.")
    else:
        feature_df = pd.DataFrame({"text": list(texts)})

    if "model_text" not in feature_df.columns:
        feature_df["model_text"] = feature_df["text"].apply(prepare_text_for_model)
    if "clean_text" not in feature_df.columns:
        feature_df["clean_text"] = feature_df["text"].apply(clean_text)
    return feature_df


def extract_pragmatic_features(texts) -> csr_matrix:
    rows: list[list[float]] = []

    for text in texts:
        raw_text = "" if text is None else str(text)
        normalized_text = raw_text.strip()
        lower_text = normalized_text.lower()
        cleaned_lower_text = clean_text(normalized_text)
        letters = [char for char in normalized_text if char.isalpha()]
        uppercase_letters = [char for char in letters if char.isupper()]
        tokens = TOKEN_PATTERN.findall(normalized_text)
        uppercase_tokens = sum(1 for token in tokens if len(token) >= 2 and token.isupper())
        positive_cue_count = sum(cleaned_lower_text.count(marker) for marker in POSITIVE_CUE_WORDS)
        negative_event_count = sum(cleaned_lower_text.count(marker) for marker in NEGATIVE_EVENT_WORDS)
        contrast_pattern_count = sum(cleaned_lower_text.count(marker) for marker in CONTRAST_PATTERNS)
        explicit_contrast_flag = int(positive_cue_count > 0 and negative_event_count > 0)
        because_dream_flag = int("because" in cleaned_lower_text and "dream" in cleaned_lower_text)
        emphasis_caps_flag = int(any(token in raw_text for token in ("SO", "VERY", "REALLY", "ТАК", "ОЧЕНЬ", "ПРЯМО")))
        emphasized_affect_count = sum(
            cleaned_lower_text.count(marker)
            for marker in (
                "так интересно",
                "так рада",
                "так рад",
                "очень интересно",
                "so interesting",
                "so happy",
                "so glad",
                "so smart",
                "so intelligent",
                "so brilliant",
                "so clever",
            )
        )
        short_emphatic_positive_flag = int(
            emphasis_caps_flag
            and len(tokens) <= 6
            and positive_cue_count == 0
            and sum(cleaned_lower_text.count(marker) for marker in ("interesting", "интересно", "рада", "рад", "smart", "intelligent", "clever", "brilliant")) > 0
        )
        compliment_pattern_count = sum(
            cleaned_lower_text.count(marker)
            for marker in (
                "ты такая умная",
                "ты такой умный",
                "youre so smart",
                "you are so smart",
                "youre so intelligent",
                "you are so intelligent",
                "youre so brilliant",
                "you are so brilliant",
                "youre so clever",
                "you are so clever",
            )
        )
        positive_opening_flag = int(
            cleaned_lower_text.startswith(
                (
                    "great",
                    "amazing",
                    "wonderful",
                    "fantastic",
                    "perfect",
                    "wow",
                    "thanks",
                    "отлично",
                    "прекрасно",
                    "ну да",
                    "ага",
                    "спасибо",
                )
            )
        )

        rows.append(
            [
                len(normalized_text),
                len(tokens),
                len(uppercase_letters) / max(len(letters), 1),
                uppercase_tokens,
                normalized_text.count("!"),
                normalized_text.count("?"),
                lower_text.count("...") + lower_text.count("…"),
                len(REPEATED_PUNCTUATION_PATTERN.findall(normalized_text)),
                len(ELONGATED_PATTERN.findall(lower_text)),
                sum(lower_text.count(marker) for marker in SARCASM_HINTS),
                sum(1 for marker in ("not", "never", "n't", "не", "нет", "ni", "no") if marker in lower_text),
                positive_cue_count,
                negative_event_count,
                contrast_pattern_count,
                explicit_contrast_flag,
                because_dream_flag,
                positive_opening_flag,
                emphasis_caps_flag,
                emphasized_affect_count,
                short_emphatic_positive_flag,
                compliment_pattern_count,
            ]
        )

    return csr_matrix(np.asarray(rows, dtype=float))


def fit_vectorizer(texts, max_features: int = MAX_FEATURES):
    feature_df = _ensure_feature_frame(texts)
    char_vectorizer = create_char_vectorizer(max_features=max_features)
    word_vectorizer = create_word_vectorizer(max_features=max_features // 2)

    char_features = char_vectorizer.fit_transform(feature_df["model_text"])
    word_features = word_vectorizer.fit_transform(feature_df["clean_text"])
    pragmatic_features = extract_pragmatic_features(feature_df["text"])

    features = hstack([char_features, word_features, pragmatic_features]).tocsr()
    feature_bundle = {
        "char_vectorizer": char_vectorizer,
        "word_vectorizer": word_vectorizer,
        "pragmatic_feature_names": [
            "text_length",
            "token_count",
            "uppercase_ratio",
            "uppercase_token_count",
            "exclamation_count",
            "question_count",
            "ellipsis_count",
            "repeated_punctuation_count",
            "elongated_character_count",
            "sarcasm_hint_count",
            "negation_hint_count",
            "positive_cue_count",
            "negative_event_count",
            "contrast_pattern_count",
            "explicit_contrast_flag",
            "because_dream_flag",
            "positive_opening_flag",
            "emphasis_caps_flag",
            "emphasized_affect_count",
            "short_emphatic_positive_flag",
            "compliment_pattern_count",
        ],
    }
    return feature_bundle, features


def transform_texts(vectorizer_bundle, texts):
    feature_df = _ensure_feature_frame(texts)
    char_features = vectorizer_bundle["char_vectorizer"].transform(feature_df["model_text"])
    word_features = vectorizer_bundle["word_vectorizer"].transform(feature_df["clean_text"])
    pragmatic_features = extract_pragmatic_features(feature_df["text"])
    return hstack([char_features, word_features, pragmatic_features]).tocsr()
