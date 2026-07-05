"""Logique métier avis + inférence LSTM."""

from django.conf import settings
from django.db import transaction

from core.ml.lstm_service import analyze_text
from core.models import InferenceLog, Review, SentimentResult


def analyze_review(review: Review, *, force: bool = False) -> SentimentResult | None:
    """Exécute le modèle LSTM et persiste le résultat + log."""
    if not force:
        existing = SentimentResult.objects.filter(review=review).first()
        if existing:
            return existing

    try:
        prediction = analyze_text(review.content)
        meets_threshold = prediction.confidence >= settings.MIN_CONFIDENCE_THRESHOLD

        with transaction.atomic():
            result, _ = SentimentResult.objects.update_or_create(
                review=review,
                defaults={
                    "sentiment": prediction.sentiment,
                    "confidence": prediction.confidence,
                    "prob_positif": prediction.prob_positif,
                    "prob_negatif": prediction.prob_negatif,
                    "prob_neutre": prediction.prob_neutre,
                    "processing_ms": prediction.processing_ms,
                    "model_version": prediction.model_version,
                },
            )
            review.status = Review.Status.ANALYZED
            if not meets_threshold:
                review.flagged = True
            review.save(update_fields=["status", "flagged"])

            InferenceLog.objects.create(
                review=review,
                status=InferenceLog.Status.SUCCESS,
                sentiment=prediction.sentiment,
                confidence=prediction.confidence,
                latency_ms=prediction.processing_ms,
                model_version=prediction.model_version,
            )
        return result

    except Exception as exc:
        InferenceLog.objects.create(
            review=review,
            status=InferenceLog.Status.ERROR,
            latency_ms=0,
            model_version=settings.LSTM_MODEL_VERSION,
            error_message=str(exc),
        )
        # Publier l'avis même si le LSTM échoue (réanalyse possible côté admin)
        review.status = Review.Status.ANALYZED
        review.save(update_fields=["status"])
        return None


def create_review(*, user, category, title: str, content: str, rating: int) -> Review:
    review = Review.objects.create(
        user=user,
        category=category,
        title=title.strip(),
        content=content.strip(),
        rating=rating,
        status=Review.Status.PENDING,
    )
    analyze_review(review)
    return review


def reanalyze_review(review: Review) -> SentimentResult | None:
    return analyze_review(review, force=True)
