"""Interface d'inférence LSTM — backend keras via ml_models/inference.py."""

from dataclasses import dataclass

from django.conf import settings


@dataclass
class SentimentPrediction:
    sentiment: str
    confidence: float
    prob_positif: float
    prob_negatif: float
    prob_neutre: float
    processing_ms: int
    model_version: str


def analyze_text(text: str) -> SentimentPrediction:
    """Point d'entrée unique pour l'analyse de sentiment."""
    backend = settings.LSTM_BACKEND
    if backend == "stub":
        from .lstm_stub import predict
        return predict(text)
    if backend == "keras":
        from .lstm_keras import predict  # noqa: F401 — branch prête pour le modèle
        return predict(text)
    raise ValueError(f"Backend LSTM inconnu : {backend}")
