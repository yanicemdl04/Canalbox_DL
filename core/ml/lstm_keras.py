"""Chargement du modèle LSTM exporté (.h5 / SavedModel).

Remplacer le corps de predict() quand le pôle IA fournit le modèle entraîné.
"""

from django.conf import settings

from .lstm_service import SentimentPrediction


def predict(text: str) -> SentimentPrediction:
    model_path = settings.LSTM_MODEL_PATH
    raise NotImplementedError(
        f"Modèle LSTM non chargé. Placez le fichier dans {model_path} "
        "et implémentez predict() avec TensorFlow/Keras."
    )
