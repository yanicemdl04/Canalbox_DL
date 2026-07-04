"""Stub LSTM — heuristiques FR en attendant le modèle TensorFlow/Keras (.h5)."""

import re
import time

from django.conf import settings

from .lstm_service import SentimentPrediction

_POS = re.compile(
    r"\b(stable|professionnel|superbe|rapide|recommand|bravo|meilleur|"
    r"réactif|soigné|dépasse|complet|fluide|content|satisfait|excellent)\b",
    re.I,
)
_NEG = re.compile(
    r"\b(frustrant|déçu|incompréhensible|effondre|redémarre|difficile|"
    r"méfiance|long|gâche|impossible|problème|prélevé|insatisfaction)\b",
    re.I,
)
_NEU = re.compile(
    r"\b(correct|globalement|perfectible|sans plus|moyen|parfois)\b",
    re.I,
)


def predict(text: str) -> SentimentPrediction:
    start = time.perf_counter()
    pos = len(_POS.findall(text))
    neg = len(_NEG.findall(text))
    neu = len(_NEU.findall(text))

    if pos > neg and pos >= neu:
        sentiment = "positif"
        raw = 0.72 + min(pos * 0.08, 0.26)
    elif neg > pos and neg >= neu:
        sentiment = "negatif"
        raw = 0.72 + min(neg * 0.08, 0.26)
    else:
        sentiment = "neutre"
        raw = 0.68 + min(neu * 0.06, 0.18)

    confidence = min(round(raw, 4), 0.99)
    rest = round(1 - confidence, 4)
    if sentiment == "positif":
        p_pos, p_neg, p_neu = confidence, rest * 0.62, rest * 0.38
    elif sentiment == "negatif":
        p_pos, p_neg, p_neu = rest * 0.4, confidence, rest * 0.6
    else:
        p_pos, p_neg, p_neu = rest * 0.55, rest * 0.45, confidence

    processing_ms = int((time.perf_counter() - start) * 1000) + 380

    return SentimentPrediction(
        sentiment=sentiment,
        confidence=confidence,
        prob_positif=round(p_pos, 4),
        prob_negatif=round(p_neg, 4),
        prob_neutre=round(p_neu, 4),
        processing_ms=processing_ms,
        model_version=settings.LSTM_MODEL_VERSION,
    )
