"""
Point d'entree backend Canal Box : nettoyage + prediction sentiment.

Usage (depuis n'importe quel dossier) :
    python models/inference.py --text "La connexion est rapide."

Usage en code :
    from models.inference import predict_sentiment
    result = predict_sentiment("Le wifi coupe tout le temps.")
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

# Reduit les logs TensorFlow avant le premier import lazy.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")

MODEL_DIR = Path(__file__).resolve().parent
MODEL_PATH = MODEL_DIR / "lstm_sentiment_model.keras"
LABEL_MAPPING_PATH = MODEL_DIR / "label_mapping.json"

_tf: Any = None
_tf_import_ms: float | None = None


def _get_tensorflow():
    """Import TensorFlow une seule fois (operation couteuse au demarrage)."""
    global _tf, _tf_import_ms
    if _tf is None:
        start = time.perf_counter()
        import tensorflow as tf

        _tf = tf
        _tf_import_ms = round((time.perf_counter() - start) * 1000, 2)
    return _tf


def clean_text(text: str) -> str:
    """Nettoie un avis client (meme logique que src/preprocess.py)."""
    text = str(text).lower().strip()
    text = re.sub(r"[^a-zàâçéèêëîïôûùüÿñæœ0-9\s']", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@lru_cache(maxsize=1)
def load_label_mapping() -> dict[int, str]:
    raw_mapping = json.loads(LABEL_MAPPING_PATH.read_text(encoding="utf-8"))
    return {int(index): label for label, index in raw_mapping.items()}


@lru_cache(maxsize=1)
def load_model():
    tf = _get_tensorflow()
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modele introuvable : {MODEL_PATH}")
    return tf.keras.models.load_model(MODEL_PATH)


def predict_sentiment(text: str, *, verbose: bool = False) -> dict:
    """Nettoie le texte, charge le modele Keras et retourne le sentiment."""
    total_start = time.perf_counter()

    if verbose:
        print("Initialisation TensorFlow...", file=sys.stderr, flush=True)
    _get_tensorflow()

    clean_start = time.perf_counter()
    cleaned = clean_text(text)
    clean_ms = round((time.perf_counter() - clean_start) * 1000, 2)

    if verbose:
        print("Chargement du modele Keras...", file=sys.stderr, flush=True)

    load_start = time.perf_counter()
    model = load_model()
    load_ms = round((time.perf_counter() - load_start) * 1000, 2)

    index_to_label = load_label_mapping()
    tf = _get_tensorflow()

    predict_start = time.perf_counter()
    probabilities = model.predict(tf.constant([cleaned], dtype=tf.string), verbose=0)[0]
    predict_ms = round((time.perf_counter() - predict_start) * 1000, 2)
    predicted_index = int(probabilities.argmax())

    total_ms = round((time.perf_counter() - total_start) * 1000, 2)
    tf_import = _tf_import_ms or 0.0

    return {
        "text_clean": cleaned,
        "sentiment": index_to_label[predicted_index],
        "confidence": round(float(probabilities[predicted_index]), 4),
        "probabilities": {
            index_to_label[i]: round(float(probabilities[i]), 4)
            for i in range(len(probabilities))
        },
        "processing_time_ms": total_ms,
        "timing_ms": {
            "tensorflow_import": tf_import,
            "model_load": load_ms,
            "predict": predict_ms,
            "clean_text": clean_ms,
            "total": total_ms,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prediction sentiment Canal Box.")
    parser.add_argument("--text", required=True, help="Commentaire client brut.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Affiche la progression du chargement sur stderr.",
    )
    args = parser.parse_args()
    print(json.dumps(predict_sentiment(args.text, verbose=args.verbose), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
