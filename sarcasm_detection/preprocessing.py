from __future__ import annotations

import re
from dataclasses import asdict

from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import TweetTokenizer

from .config import PreprocessingConfig

URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
MENTION_PATTERN = re.compile(r"@\w+")
HASHTAG_PATTERN = re.compile(r"#(\w+)")
SPACE_PATTERN = re.compile(r"\s+")


class SocialTextPreprocessor:
    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()
        self.tokenizer = TweetTokenizer(strip_handles=False, reduce_len=True, preserve_case=not self.config.lowercase)
        self.stopwords = set(stopwords.words("english")) if self.config.remove_stopwords else set()
        self.negations = {"no", "not", "never", "none", "n't"}
        if self.config.keep_negations:
            self.stopwords -= self.negations
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()

    def clean_text(self, text: str) -> str:
        working = text
        if self.config.remove_urls:
            working = URL_PATTERN.sub(" ", working)
        if self.config.remove_mentions:
            working = MENTION_PATTERN.sub(" ", working)
        if self.config.normalize_hashtags:
            working = HASHTAG_PATTERN.sub(r" \1 ", working)
        working = SPACE_PATTERN.sub(" ", working).strip()
        return working.lower() if self.config.lowercase else working

    def normalize_token(self, token: str) -> str | None:
        if token in {"!", "?", "..."}:
            return token
        if not any(char.isalnum() for char in token):
            return None
        if len(token) < self.config.min_token_length and token not in {"i", "a"}:
            return None
        if self.config.remove_stopwords and token in self.stopwords:
            return None

        normalized = token
        if self.config.apply_lemmatization:
            normalized = self.lemmatizer.lemmatize(normalized)
        if self.config.apply_stemming:
            normalized = self.stemmer.stem(normalized)
        return normalized

    def preprocess_text(self, text: str) -> str:
        cleaned = self.clean_text(str(text))
        tokens = self.tokenizer.tokenize(cleaned)
        normalized_tokens = []
        for token in tokens:
            normalized = self.normalize_token(token)
            if normalized:
                normalized_tokens.append(normalized)
        return " ".join(normalized_tokens)

    def transform(self, texts: list[str]) -> list[str]:
        return [self.preprocess_text(text) for text in texts]

    def get_config_dict(self) -> dict[str, object]:
        return asdict(self.config)

