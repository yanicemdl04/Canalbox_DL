"""Statistiques dynamiques pour le tableau de bord admin."""

from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone

from core.models import Category, InferenceLog, Review, SentimentResult, User

DAY_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


def _format_total(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def client_stats(user):
    qs = Review.objects.filter(user=user)
    published = qs.filter(status=Review.Status.ANALYZED).count()
    avg = qs.aggregate(v=Avg("rating"))["v"]
    categories_used = qs.values("category_id").distinct().count()
    return {
        "my_reviews": qs.count(),
        "published": published,
        "avg_rating": round(avg, 1) if avg else 0,
        "categories_used": categories_used,
    }


def dashboard_stats():
    total = Review.objects.filter(status=Review.Status.ANALYZED).count()
    results = SentimentResult.objects.all()
    pos = results.filter(sentiment=SentimentResult.Sentiment.POSITIF).count()
    neg = results.filter(sentiment=SentimentResult.Sentiment.NEGATIF).count()
    neu = results.filter(sentiment=SentimentResult.Sentiment.NEUTRE).count()
    analyzed = max(pos + neg + neu, 1)

    avg_rating = Review.objects.aggregate(v=Avg("rating"))["v"] or 0
    avg_conf = results.aggregate(v=Avg("confidence"))["v"] or 0
    avg_lat = results.aggregate(v=Avg("processing_ms"))["v"] or 0

    satisfaction = round(pos / analyzed * 100) if analyzed else 0

    now = timezone.localtime()
    trend = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        day_results = results.filter(analyzed_at__date=day)
        day_total = day_results.count() or 1
        d_pos = day_results.filter(sentiment=SentimentResult.Sentiment.POSITIF).count()
        d_neg = day_results.filter(sentiment=SentimentResult.Sentiment.NEGATIF).count()
        d_neu = day_results.filter(sentiment=SentimentResult.Sentiment.NEUTRE).count()
        trend.append({
            "day": DAY_LABELS[day.weekday()],
            "pos": round(d_pos / day_total * 100),
            "neg": round(d_neg / day_total * 100),
            "neu": round(d_neu / day_total * 100),
        })

    by_category = []
    for cat in Category.objects.annotate(review_count=Count("reviews")):
        cat_results = results.filter(review__category=cat)
        cat_total = cat_results.count() or 1
        cat_pos = cat_results.filter(sentiment=SentimentResult.Sentiment.POSITIF).count()
        by_category.append({
            "name": cat.name,
            "value": cat.review_count,
            "pct": round(cat.review_count / max(total, 1) * 100),
            "sentiment": round(cat_pos / cat_total * 100),
        })

    return {
        "total": total,
        "total_label": _format_total(total),
        "positive": pos,
        "negative": neg,
        "neutral": neu,
        "positive_pct": round(pos / analyzed * 100),
        "negative_pct": round(neg / analyzed * 100),
        "neutral_pct": round(neu / analyzed * 100),
        "avg_rating": round(avg_rating, 2),
        "avg_confidence": round(avg_conf, 2),
        "avg_confidence_pct": round(avg_conf * 100),
        "avg_latency": round(avg_lat),
        "satisfaction": satisfaction,
        "trend": trend,
        "by_category": by_category,
    }


def inference_log_stats():
    logs = InferenceLog.objects.all()
    total = logs.count()
    success = logs.filter(status=InferenceLog.Status.SUCCESS).count()
    errors = logs.filter(status=InferenceLog.Status.ERROR).count()
    median_lat = logs.filter(status=InferenceLog.Status.SUCCESS).aggregate(v=Avg("latency_ms"))["v"] or 0
    success_rate = round(success / total * 100, 1) if total else 100.0
    return {
        "total": total,
        "success_rate": success_rate,
        "median_latency": round(median_lat),
        "errors_30d": errors,
    }


def user_admin_stats():
    clients = User.objects.filter(role=User.Role.CLIENT).count()
    admins = User.objects.filter(role=User.Role.ADMIN).count()
    actifs = User.objects.filter(status=User.Status.ACTIF).count()
    suspendus = User.objects.filter(status=User.Status.SUSPENDU).count()
    return {
        "clients": clients,
        "admins": admins,
        "actifs": actifs,
        "suspendus": suspendus,
    }
