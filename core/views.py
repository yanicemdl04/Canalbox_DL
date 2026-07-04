"""Vues de l'interface Canal Box.

Le backend réel (API REST, LSTM, JWT, RLS) est déjà défini par ailleurs.
Ces vues rendent uniquement les templates avec des données de démonstration
et simulent l'authentification par session pour rendre l'UI navigable.

Règle de rôle stricte : les données de sentiment / score LSTM ne sont
transmises qu'aux templates de l'espace administrateur.
"""
from functools import wraps

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render

from . import demo_data


# --- Simulation d'authentification par session ------------------------------
def current_user(request):
    role = request.session.get("role")
    if role in demo_data.DEMO_USERS:
        return demo_data.DEMO_USERS[role]
    return None


def login_required_demo(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not current_user(request):
            return redirect("login")
        return view(request, *args, **kwargs)
    return wrapper


def admin_required_demo(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = current_user(request)
        if not user:
            return redirect("login")
        if user["role"] != "admin":
            return redirect("client_dashboard")
        return view(request, *args, **kwargs)
    return wrapper


def _base_ctx(request, **extra):
    ctx = {"user": current_user(request)}
    ctx.update(extra)
    return ctx


# --- Partie publique ---------------------------------------------------------
def landing(request):
    return render(request, "public/landing.html", _base_ctx(
        request,
        categories=demo_data.CATEGORIES,
        reviews=demo_data.REVIEWS[:3],
    ))


def login_view(request):
    # Connexion rapide de démonstration : /connexion/?demo=admin (ou client)
    demo = request.GET.get("demo")
    if demo in demo_data.DEMO_USERS:
        request.session["role"] = demo
        return redirect("admin_dashboard" if demo == "admin" else "client_dashboard")
    if request.method == "POST":
        role = request.POST.get("role", "client")
        if role not in demo_data.DEMO_USERS:
            role = "client"
        request.session["role"] = role
        user = demo_data.DEMO_USERS[role]
        messages.success(request, f"Bienvenue {user['name'].split()[0]} !")
        return redirect("admin_dashboard" if role == "admin" else "client_dashboard")
    return render(request, "public/login.html", _base_ctx(request))


def register_view(request):
    if request.method == "POST":
        request.session["role"] = "client"
        messages.success(request, "Votre compte Canal Box a été créé avec succès.")
        return redirect("client_dashboard")
    return render(request, "public/register.html", _base_ctx(request, categories=demo_data.CATEGORIES))


def forgot_password_view(request):
    if request.method == "POST":
        messages.success(request, "Un lien de réinitialisation vient d'être envoyé.")
        return redirect("login")
    return render(request, "public/forgot_password.html", _base_ctx(request))


def logout_view(request):
    request.session.flush()
    return redirect("landing")


# --- Espace client -----------------------------------------------------------
def _client_review(review):
    """Vue client : on masque toute donnée IA (sentiment/score)."""
    return {k: v for k, v in review.items()
            if k not in ("sentiment", "confidence", "processing_ms", "flagged")}


@login_required_demo
def client_dashboard(request):
    user = current_user(request)
    reviews = [_client_review(r) for r in demo_data.REVIEWS if True][:5]
    stats = {
        "my_reviews": 12,
        "published": 12,
        "avg_rating": 4.2,
        "categories_used": 3,
    }
    return render(request, "client/dashboard.html", _base_ctx(
        request, reviews=reviews, stats=stats, categories=demo_data.CATEGORIES))


@login_required_demo
def client_reviews(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("categorie", "")
    note = request.GET.get("note", "")
    reviews = [_client_review(r) for r in demo_data.REVIEWS]
    if q:
        reviews = [r for r in reviews if q.lower() in (r["title"] + r["content"]).lower()]
    if cat:
        reviews = [r for r in reviews if r["category"]["slug"] == cat]
    if note:
        reviews = [r for r in reviews if str(r["rating"]) == note]
    return render(request, "client/reviews.html", _base_ctx(
        request, reviews=reviews, categories=demo_data.CATEGORIES,
        q=q, active_cat=cat, active_note=note, total=len(reviews)))


@login_required_demo
def client_review_detail(request, review_id):
    review = demo_data.get_review(review_id)
    if not review:
        return render(request, "client/review_detail.html", _base_ctx(request, review=None), status=404)
    related = [_client_review(r) for r in demo_data.REVIEWS
               if r["category"]["id"] == review["category"]["id"] and r["id"] != review["id"]][:3]
    return render(request, "client/review_detail.html", _base_ctx(
        request, review=_client_review(review), related=related))


@login_required_demo
def client_review_create(request):
    if request.method == "POST":
        messages.success(request, "Votre avis a été publié. Merci pour votre retour !")
        return redirect("client_reviews")
    return render(request, "client/review_create.html", _base_ctx(
        request, categories=demo_data.CATEGORIES))


@login_required_demo
def client_profile(request):
    return render(request, "client/profile.html", _base_ctx(
        request, reviews=[_client_review(r) for r in demo_data.REVIEWS[:4]]))


@login_required_demo
def client_profile_edit(request):
    if request.method == "POST":
        messages.success(request, "Votre profil a été mis à jour.")
        return redirect("client_profile")
    return render(request, "client/profile_edit.html", _base_ctx(request))


# --- Espace administrateur ---------------------------------------------------
@admin_required_demo
def admin_dashboard(request):
    return render(request, "adminpanel/dashboard.html", _base_ctx(
        request, stats=demo_data.dashboard_stats(),
        reviews=demo_data.REVIEWS[:5], logs=demo_data.INFERENCE_LOGS[:4]))


@admin_required_demo
def admin_reviews(request):
    q = request.GET.get("q", "").strip()
    sentiment = request.GET.get("sentiment", "")
    cat = request.GET.get("categorie", "")
    reviews = list(demo_data.REVIEWS)
    if q:
        reviews = [r for r in reviews if q.lower() in (r["title"] + r["content"]).lower()]
    if sentiment:
        reviews = [r for r in reviews if r["sentiment"] == sentiment]
    if cat:
        reviews = [r for r in reviews if r["category"]["slug"] == cat]
    return render(request, "adminpanel/reviews.html", _base_ctx(
        request, reviews=reviews, categories=demo_data.CATEGORIES,
        q=q, active_sentiment=sentiment, active_cat=cat, total=len(reviews)))


@admin_required_demo
def admin_review_detail(request, review_id):
    review = demo_data.get_review(review_id)
    probs = None
    if review:
        conf = review["confidence"]
        rest = round((1 - conf), 4)
        # Distribution softmax simulée (le maximum correspond à la classe prédite)
        order = {"positif": (conf, rest * 0.62, rest * 0.38),
                 "negatif": (rest * 0.4, conf, rest * 0.6),
                 "neutre": (rest * 0.55, rest * 0.45, conf)}
        p_pos, p_neg, p_neu = order.get(review["sentiment"], (conf, rest / 2, rest / 2))
        probs = {
            "positif": round(p_pos * 100, 1),
            "negatif": round(p_neg * 100, 1),
            "neutre": round(p_neu * 100, 1),
        }
    return render(request, "adminpanel/review_detail.html", _base_ctx(
        request, review=review, probs=probs))


@admin_required_demo
def admin_reanalyze(request, review_id):
    messages.success(request, f"Réanalyse LSTM relancée pour l'avis #{review_id}.")
    return redirect("admin_review_detail", review_id=review_id)


@admin_required_demo
def admin_delete_review(request, review_id):
    messages.success(request, f"Avis #{review_id} supprimé et modéré.")
    return redirect("admin_reviews")


@admin_required_demo
def admin_users(request):
    return render(request, "adminpanel/users.html", _base_ctx(
        request, users=demo_data.admin_users()))


@admin_required_demo
def admin_categories(request):
    if request.method == "POST":
        messages.success(request, "Catégorie enregistrée.")
        return redirect("admin_categories")
    return render(request, "adminpanel/categories.html", _base_ctx(
        request, categories=demo_data.CATEGORIES))


@admin_required_demo
def admin_logs(request):
    return render(request, "adminpanel/logs.html", _base_ctx(
        request, logs=demo_data.INFERENCE_LOGS, stats=demo_data.dashboard_stats()))


@admin_required_demo
def admin_moderation(request):
    flagged = [r for r in demo_data.REVIEWS if r["flagged"]]
    return render(request, "adminpanel/moderation.html", _base_ctx(
        request, reviews=flagged))


@admin_required_demo
def admin_export_csv(request):
    import csv
    from io import StringIO
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "titre", "note", "categorie", "sentiment", "confiance", "latence_ms", "date"])
    for r in demo_data.REVIEWS:
        writer.writerow([r["id"], r["title"], r["rating"], r["category"]["name"],
                         r["sentiment"], r["confidence"], r["processing_ms"], r["created_label"]])
    resp = HttpResponse(buf.getvalue(), content_type="text/csv")
    resp["Content-Disposition"] = "attachment; filename=canalbox_avis.csv"
    return resp


@admin_required_demo
def admin_export_pdf(request):
    # Démo : renvoie une confirmation. Le backend réel génère le PDF.
    messages.success(request, "Export PDF généré (démo).")
    return redirect("admin_dashboard")
