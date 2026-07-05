"""Inférence BiLSTM — délègue à ml_models/inference.py (modèle officiel Canal Box)."""

from __future__ import annotations

from django.conf import settings

from .lstm_service import SentimentPrediction

# Labels du modèle (EN) → valeurs stockées en base (FR)
_SENTIMENT_MAP = {
    "negative": "negatif",
    "neutral": "neutre",
    "positive": "positif",
}


def _inference():
    from ml_models.inference import load_model, predict_sentiment

    return load_model, predict_sentiment


def _get_model():
    load_model, _ = _inference()
    return load_model()


def predict(text: str) -> SentimentPrediction:
    load_model, predict_sentiment = _inference()
    load_model()  # no-op si déjà chargé (lru_cache)
    result = predict_sentiment(text, verbose=False)

    probs = result["probabilities"]
    timing = result.get("timing_ms") or {}
    processing_ms = int(timing.get("predict") or result["processing_time_ms"])

    sentiment_en = result["sentiment"]
    sentiment = _SENTIMENT_MAP.get(sentiment_en, sentiment_en)

    return SentimentPrediction(
        sentiment=sentiment,
        confidence=result["confidence"],
        prob_negatif=probs.get("negative", 0.0),
        prob_neutre=probs.get("neutral", 0.0),
        prob_positif=probs.get("positive", 0.0),
        processing_ms=processing_ms,
        model_version=settings.LSTM_MODEL_VERSION,
    )
