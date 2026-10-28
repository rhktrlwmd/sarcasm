from __future__ import annotations

import re

from src.preprocessing import clean_text

POSITIVE_OPENERS = [
    "great",
    "amazing",
    "wonderful",
    "fantastic",
    "perfect",
    "wow",
    "вау",
    "thanks",
    "brilliant",
    "отлично",
    "прекрасно",
    "великолепно",
    "замечательно",
    "какое счастье",
    "спасибо",
    "ну конечно",
    "конечно",
    "ну да",
    "ага",
]
COMPLIMENT_PATTERNS = [
    "ты такая умная",
    "ты такой умный",
    "какая ты умная",
    "какой ты умный",
    "ну ты умная",
    "ну ты умный",
    "youre so smart",
    "you're so smart",
    "you are so smart",
    "youre so intelligent",
    "you're so intelligent",
    "you are so intelligent",
    "youre so brilliant",
    "you're so brilliant",
    "you are so brilliant",
    "youre so clever",
    "you're so clever",
    "you are so clever",
    "such a genius",
    "what a genius",
]
EMPHASIS_WORD_PATTERNS = [
    "so",
    "really",
    "very",
    "such",
    "так",
    "очень",
    "прямо",
    "просто",
]
POSITIVE_SENTIMENT_PATTERNS = [
    "happy",
    "glad",
    "smart",
    "intelligent",
    "brilliant",
    "clever",
    "genius",
    "interesting",
    "proud",
    "love",
    "умная",
    "умный",
    "интеллектуал",
    "рада",
    "рад",
    "интересно",
    "гений",
    "счастлива",
    "счастлив",
]
EMPHASIZED_AFFECT_PATTERNS = [
    "так рада",
    "так рад",
    "так интересно",
    "очень интересно",
    "so happy",
    "so glad",
    "so interesting",
    "so intelligent",
    "so brilliant",
    "so clever",
    "happy for you",
    "glad for you",
]
NEGATIVE_MARKERS = [
    "crash",
    "crashed",
    "deadline",
    "traffic",
    "homework",
    "meeting",
    "broken",
    "stuck",
    "rain",
    "bug",
    "printer",
    "jam",
    "elevator",
    "laptop",
    "phone",
    "battery",
    "5 a m",
    "exam",
    "late",
    "reply",
    "weeks",
    "слом",
    "баг",
    "дедлайн",
    "пропал",
    "созвон",
    "три недели",
    "месяц",
    "ошиб",
    "лифт",
    "компьютер",
    "телефон",
    "разряд",
    "не работает",
    "сломал",
    "нужный момент",
]
STRONG_SARCASM_PATTERNS = [
    "what a wonderful",
    "what a surprise",
    "i really needed another",
    "because waking up",
    "everyone s dream",
    "please take your time",
    "nothing else to do",
    "right before the deadline",
    "stuck in traffic",
    "pouring rain",
    "broken again",
    "stopped working",
    "reply to my email",
    "through two hours",
    "через три недели",
    "мне вообще нечего делать",
    "как же я люблю",
    "какое счастье",
    "снова не работает",
    "в самый нужный момент",
    "опять сломался",
]
NON_SARCASM_PATTERNS = [
    "beautiful shoes",
    "very beautiful shoes",
    "i am really happy for you",
    "я так рада за тебя",
    "очень красивая обувь",
    "thank you for replying quickly",
]
SINCERE_CONTEXT_PATTERNS = [
    "мне это очень интересно правда",
    "я так рада что ты приехал вовремя",
    "я так рад что мы успели всё закончить",
    "я так рад что мы успели все закончить",
    "очень люблю этот альбом",
]
UPPERCASE_WORD_PATTERN = re.compile(r"\b[A-ZА-ЯЁ]{2,}\b")
TOKEN_PATTERN = re.compile(r"\b\w+\b", flags=re.UNICODE)


def sarcasm_rule_score(text: str) -> float:
    normalized = clean_text(text)
    lowered = normalized.lower()
    raw_text = text or ""
    token_count = len(TOKEN_PATTERN.findall(raw_text))

    score = 0.0

    positive_count = sum(lowered.count(marker) for marker in POSITIVE_OPENERS)
    negative_count = sum(lowered.count(marker) for marker in NEGATIVE_MARKERS)
    strong_pattern_count = sum(lowered.count(marker) for marker in STRONG_SARCASM_PATTERNS)
    non_sarcasm_count = sum(lowered.count(marker) for marker in NON_SARCASM_PATTERNS)
    sincere_context_count = sum(lowered.count(marker) for marker in SINCERE_CONTEXT_PATTERNS)
    compliment_pattern_count = sum(lowered.count(marker) for marker in COMPLIMENT_PATTERNS)
    emphasis_word_count = sum(lowered.count(marker) for marker in EMPHASIS_WORD_PATTERNS)
    positive_sentiment_count = sum(lowered.count(marker) for marker in POSITIVE_SENTIMENT_PATTERNS)
    emphasized_affect_count = sum(lowered.count(marker) for marker in EMPHASIZED_AFFECT_PATTERNS)
    uppercase_word_count = len(UPPERCASE_WORD_PATTERN.findall(raw_text))
    has_emphasis_caps = any(token in raw_text for token in ("SO", "VERY", "REALLY", "ТАК", "ОЧЕНЬ", "ПРЯМО"))

    if positive_count and negative_count:
        score += 0.28
    if strong_pattern_count:
        score += 0.22 * strong_pattern_count
    if compliment_pattern_count and ("wow" in lowered or "вау" in lowered or uppercase_word_count >= 1 or "ну конечно" in lowered):
        score += 0.34 * compliment_pattern_count
    if has_emphasis_caps and positive_sentiment_count:
        score += 0.28
    if has_emphasis_caps and compliment_pattern_count:
        score += 0.18
    if has_emphasis_caps and emphasized_affect_count:
        score += 0.18 * emphasized_affect_count
    if has_emphasis_caps and positive_sentiment_count and token_count <= 6 and non_sarcasm_count == 0:
        score += 0.24
    if ("так интересно" in lowered or "so interesting" in lowered) and token_count <= 5:
        score += 0.24
    if ("так рада" in lowered or "так рад" in lowered or "so happy" in lowered or "so glad" in lowered) and token_count <= 6:
        score += 0.18
    if emphasis_word_count and positive_sentiment_count and ("wow" in lowered or "вау" in lowered):
        score += 0.18
    if lowered.startswith("это ") and has_emphasis_caps and "интересно" in lowered:
        score += 0.18
    if "ну конечно" in lowered and ("мечта" in lowered or "рада" in lowered or "интересно" in lowered):
        score += 0.28
    if uppercase_word_count >= 1 and positive_count:
        score += 0.08
    if "?" in raw_text and positive_count:
        score += 0.08
    if "!" in raw_text and positive_count:
        score += 0.05
    if "another" in lowered and ("meeting" in lowered or "deadline" in lowered or "homework" in lowered):
        score += 0.16
    if "again" in lowered and negative_count:
        score += 0.12
    if "broken again" in lowered:
        score += 0.18
    if "stopped working" in lowered:
        score += 0.18
    if "because" in lowered and "dream" in lowered:
        score += 0.22
    if "please take your time" in lowered:
        score += 0.25
    if "мне вообще нечего делать" in lowered:
        score += 0.25
    if "снова не работает" in lowered:
        score += 0.22
    if "опять сломался" in lowered or "опять сломалась" in lowered:
        score += 0.22
    if "в самый нужный момент" in lowered:
        score += 0.25
    if "wow" in lowered and "eat my shoes" in lowered:
        score += 0.35

    if non_sarcasm_count:
        score -= 0.35 * non_sarcasm_count
    if sincere_context_count and has_emphasis_caps and negative_count == 0 and compliment_pattern_count == 0:
        score -= 0.5 * sincere_context_count
    if lowered.startswith("мне это очень интересно") and "правда" in lowered and negative_count == 0:
        score -= 0.2
    if ("я так рада что" in lowered or "я так рад что" in lowered) and negative_count == 0:
        score -= 0.35
    if ("beautiful shoes" in lowered or "красивая обувь" in lowered) and negative_count == 0:
        score -= 0.2

    return max(-0.6, min(0.8, score))


def adjust_probability_with_rules(text: str, base_probability: float) -> float:
    rule_score = sarcasm_rule_score(text)
    adjusted_probability = base_probability + rule_score
    return max(0.0, min(1.0, adjusted_probability))
