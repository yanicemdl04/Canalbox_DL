"""Conversion ORM → dicts compatibles avec les templates existants."""

from django.utils import timezone

FR_MONTHS_SHORT = [
    "Jan", "Fév", "Mar", "Avr", "Mai", "Juin",
    "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc",
]


def format_datetime(dt):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    month = FR_MONTHS_SHORT[dt.month - 1]
    return dt.strftime(f"%d {month} %Y · %Hh%M")


def format_datetime_short(dt):
    if timezone.is_aware(dt):
        dt = timezone.localtime(dt)
    month = FR_MONTHS_SHORT[dt.month - 1]
    return dt.strftime(f"%d {month} · %Hh%M")


def user_to_dict(user):
    return {
        "id": user.id,
        "name": user.display_name,
        "email": user.email,
        "role": user.role,
        "initials": user.initials,
        "plan": user.plan,
        "member_since": user.member_since,
        "avatar_color": user.avatar_color,
        "status": user.status,
    }


def category_to_dict(category, review_count=None):
    count = review_count if review_count is not None else category.reviews.count()
    return {
        "id": category.id,
        "name": category.name,
        "slug": category.slug,
        "description": category.description,
        "count": count,
        "icon": category.icon,
    }


def review_to_dict(review, *, include_ia=False):
    author = review.user.display_name
    data = {
        "id": review.id,
        "title": review.title,
        "content": review.content,
        "excerpt": review.content[:120] + ("…" if len(review.content) > 120 else ""),
        "rating": review.rating,
        "author": author,
        "initials": review.user.initials,
        "category": category_to_dict(review.category),
        "created_at": review.created_at,
        "created_label": format_datetime(review.created_at),
        "status": "analysé" if review.status == review.Status.ANALYZED else "en attente",
    }
    if include_ia:
        sr = getattr(review, "sentiment_result", None)
        data["flagged"] = review.flagged
        if sr:
            data["sentiment"] = sr.sentiment
            data["confidence"] = sr.confidence
            data["processing_ms"] = sr.processing_ms
            data["model_version"] = sr.model_version
        else:
            data["sentiment"] = "neutre"
            data["confidence"] = 0.0
            data["processing_ms"] = 0
            data["model_version"] = "—"
    return data


def probs_from_result(sr):
    if not sr:
        return {"positif": 0, "negatif": 0, "neutre": 0}
    return {
        "positif": round(sr.prob_positif * 100, 1),
        "negatif": round(sr.prob_negatif * 100, 1),
        "neutre": round(sr.prob_neutre * 100, 1),
    }


def inference_log_to_dict(log):
    return {
        "id": log.id,
        "review_id": log.review_id,
        "status": log.status,
        "sentiment": log.sentiment or "—",
        "confidence": log.confidence,
        "latency": log.latency_ms,
        "ts": format_datetime_short(log.created_at),
        "model": log.model_version,
    }


def admin_user_to_dict(user):
    return {
        "id": user.id,
        "name": user.display_name,
        "initials": user.initials,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "reviews": user.reviews.count(),
        "joined": user.date_joined.strftime("%d %b %Y"),
    }
