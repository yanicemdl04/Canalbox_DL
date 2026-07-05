from django import template

register = template.Library()


@register.filter
def times(number):
    """Renvoie une plage pour boucler N fois dans un template."""
    try:
        return range(int(number))
    except (TypeError, ValueError):
        return range(0)


@register.filter
def remaining_stars(rating):
    try:
        return range(5 - int(rating))
    except (TypeError, ValueError):
        return range(5)


@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return 0


@register.filter
def pct(value):
    """0.91 -> 91"""
    try:
        return round(float(value) * 100)
    except (TypeError, ValueError):
        return 0


@register.filter
def sentiment_label(value):
    if not value:
        return "Non analysé"
    return {"positif": "Positif", "negatif": "Négatif", "neutre": "Neutre"}.get(value, value)


@register.filter
def sentiment_badge(value):
    return {"positif": "badge-pos", "negatif": "badge-neg", "neutre": "badge-neu"}.get(value, "badge-neutral")


@register.filter
def sentiment_color(value):
    return {"positif": "var(--sent-pos)", "negatif": "var(--sent-neg)", "neutre": "var(--sent-neu)"}.get(value, "var(--cb-mist)")


@register.filter
def cat_icon(slug):
    return {"internet": "i-wifi", "tv": "i-tv", "sav": "i-headset", "facturation": "i-receipt"}.get(slug, "i-folder")
