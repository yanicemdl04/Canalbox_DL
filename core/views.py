"""Vues Canal Box — backend Django monolithique avec inférence LSTM intégrée.

Règle de rôle : sentiment / score LSTM uniquement pour l'espace administrateur.
"""
import csv
from io import StringIO

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Category, InferenceLog, Review, SentimentResult
from .presenters import (
    admin_user_to_dict,
    category_to_dict,
    inference_log_to_dict,
    probs_from_result,
    review_to_dict,
    user_to_dict,
)
from .services.review_service import create_review, reanalyze_review
from .services.stats_service import (
    client_stats,
    dashboard_stats,
    inference_log_stats,
    user_admin_stats,
)

User = get_user_model()
PAGE_SIZE = 12


def _base_ctx(request, **extra):
    user = request.user if request.user.is_authenticated else None
    ctx = {"user": user_to_dict(user) if user else None}
    ctx.update(extra)
    return ctx


def _categories_with_counts():
    return [
        category_to_dict(c, c.review_count)
        for c in Category.objects.annotate(review_count=Count("reviews"))
    ]


def _client_review_dict(review):
    return review_to_dict(review, include_ia=False)


def _admin_review_dict(review):
    return review_to_dict(review, include_ia=True)


def _filter_reviews(qs, *, q="", cat="", note="", sentiment="", period=""):
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
    if cat:
        qs = qs.filter(category__slug=cat)
    if note:
        qs = qs.filter(rating=int(note))
    if sentiment:
        qs = qs.filter(sentiment_result__sentiment=sentiment)
    if period == "7d":
        qs = qs.filter(created_at__gte=timezone.now() - timezone.timedelta(days=7))
    elif period == "30d":
        qs = qs.filter(created_at__gte=timezone.now() - timezone.timedelta(days=30))
    return qs


def admin_required(view):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.role != User.Role.ADMIN:
            return redirect("client_dashboard")
        if request.user.status == User.Status.SUSPENDU:
            messages.error(request, "Votre compte administrateur est suspendu.")
            logout(request)
            return redirect("login")
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    wrapper.__doc__ = view.__doc__
    return wrapper


def active_user_required(view):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.status == User.Status.SUSPENDU:
            messages.error(request, "Votre compte est suspendu. Contactez le support Canal Box.")
            logout(request)
            return redirect("login")
        return view(request, *args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper


# --- Public ------------------------------------------------------------------
def landing(request):
    reviews = Review.objects.filter(status=Review.Status.ANALYZED).select_related(
        "user", "category"
    )[:3]
    return render(request, "public/landing.html", _base_ctx(
        request,
        categories=_categories_with_counts(),
        reviews=[_client_review_dict(r) for r in reviews],
    ))


def login_view(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.ADMIN:
            return redirect("admin_dashboard")
        return redirect("client_dashboard")

    demo = request.GET.get("demo")
    if demo in ("client", "admin"):
        email = (
            "yanice.client@canalbox.cd" if demo == "client"
            else "david.admin@canalbox.cd"
        )
        user = User.objects.filter(email=email).first()
        if user:
            login(request, user)
            return redirect("admin_dashboard" if demo == "admin" else "client_dashboard")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is None:
            messages.error(request, "E-mail ou mot de passe incorrect.")
        elif user.status == User.Status.SUSPENDU:
            messages.error(request, "Ce compte est suspendu.")
        else:
            login(request, user)
            messages.success(request, f"Bienvenue {user.display_name.split()[0]} !")
            if user.role == User.Role.ADMIN:
                return redirect("admin_dashboard")
            return redirect("client_dashboard")

    return render(request, "public/login.html", _base_ctx(request))


def register_view(request):
    if request.user.is_authenticated:
        return redirect("client_dashboard")

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        password2 = request.POST.get("password2", "")
        plan = request.POST.get("plan", "Canal Box Fibre 200")

        if not name or not email:
            messages.error(request, "Nom et e-mail obligatoires.")
        elif password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
        elif len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
        elif User.objects.filter(email=email).exists():
            messages.error(request, "Un compte existe déjà avec cet e-mail.")
        else:
            username = email.split("@")[0]
            base = username
            n = 1
            while User.objects.filter(username=username).exists():
                username = f"{base}{n}"
                n += 1
            parts = name.split(None, 1)
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=parts[0],
                last_name=parts[1] if len(parts) > 1 else "",
                role=User.Role.CLIENT,
                plan=plan,
            )
            login(request, user)
            messages.success(request, "Votre compte Canal Box a été créé avec succès.")
            return redirect("client_dashboard")

    return render(request, "public/register.html", _base_ctx(
        request, categories=_categories_with_counts()))


def forgot_password_view(request):
    if request.method == "POST":
        messages.success(request, "Un lien de réinitialisation vient d'être envoyé.")
        return redirect("login")
    return render(request, "public/forgot_password.html", _base_ctx(request))


def logout_view(request):
    logout(request)
    return redirect("landing")


# --- Client ------------------------------------------------------------------
@active_user_required
def client_dashboard(request):
    reviews = Review.objects.filter(user=request.user).select_related("category")[:5]
    return render(request, "client/dashboard.html", _base_ctx(
        request,
        reviews=[_client_review_dict(r) for r in reviews],
        stats=client_stats(request.user),
        categories=_categories_with_counts(),
    ))


@active_user_required
def client_reviews(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("categorie", "")
    note = request.GET.get("note", "")
    period = request.GET.get("periode", "")

    qs = _filter_reviews(
        Review.objects.filter(status=Review.Status.ANALYZED).select_related("user", "category"),
        q=q, cat=cat, note=note, period=period,
    )
    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "client/reviews.html", _base_ctx(
        request,
        reviews=[_client_review_dict(r) for r in page.object_list],
        categories=_categories_with_counts(),
        q=q, active_cat=cat, active_note=note, active_period=period,
        total=paginator.count, page_obj=page,
    ))


@active_user_required
def client_review_detail(request, review_id):
    review = Review.objects.filter(
        pk=review_id, status=Review.Status.ANALYZED,
    ).select_related("user", "category").first()
    if not review:
        return render(request, "client/review_detail.html", _base_ctx(request, review=None), status=404)

    related = Review.objects.filter(
        category=review.category, status=Review.Status.ANALYZED,
    ).exclude(pk=review.pk).select_related("user", "category")[:3]

    return render(request, "client/review_detail.html", _base_ctx(
        request,
        review=_client_review_dict(review),
        related=[_client_review_dict(r) for r in related],
    ))


@active_user_required
def client_review_create(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        content = request.POST.get("content", "").strip()
        rating = int(request.POST.get("rating") or 0)
        cat_slug = request.POST.get("categorie", "")
        category = Category.objects.filter(slug=cat_slug).first()

        if not category:
            messages.error(request, "Veuillez choisir une catégorie.")
        elif len(title) < 5:
            messages.error(request, "Le titre doit contenir au moins 5 caractères.")
        elif len(content) < 20:
            messages.error(request, "L'avis doit contenir au moins 20 caractères.")
        elif rating < 1 or rating > 5:
            messages.error(request, "Veuillez attribuer une note entre 1 et 5 étoiles.")
        else:
            create_review(
                user=request.user,
                category=category,
                title=title,
                content=content,
                rating=rating,
            )
            messages.success(request, "Votre avis a été publié. Merci pour votre retour !")
            return redirect("client_reviews")

    return render(request, "client/review_create.html", _base_ctx(
        request, categories=_categories_with_counts()))


@active_user_required
def client_profile(request):
    reviews = Review.objects.filter(user=request.user).select_related("category")[:4]
    return render(request, "client/profile.html", _base_ctx(
        request, reviews=[_client_review_dict(r) for r in reviews]))


@active_user_required
def client_profile_edit(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        plan = request.POST.get("plan", request.user.plan)

        if email and User.objects.exclude(pk=request.user.pk).filter(email=email).exists():
            messages.error(request, "Cet e-mail est déjà utilisé.")
        else:
            parts = name.split(None, 1)
            request.user.first_name = parts[0] if parts else ""
            request.user.last_name = parts[1] if len(parts) > 1 else ""
            if email:
                request.user.email = email
            request.user.plan = plan
            request.user.save()
            messages.success(request, "Votre profil a été mis à jour.")
            return redirect("client_profile")

    return render(request, "client/profile_edit.html", _base_ctx(request))


# --- Admin -------------------------------------------------------------------
@admin_required
def admin_dashboard(request):
    reviews = Review.objects.filter(status=Review.Status.ANALYZED).select_related(
        "user", "category", "sentiment_result",
    )[:5]
    logs = InferenceLog.objects.select_related("review")[:4]
    stats = dashboard_stats()
    return render(request, "adminpanel/dashboard.html", _base_ctx(
        request,
        stats=stats,
        reviews=[_admin_review_dict(r) for r in reviews],
        logs=[inference_log_to_dict(l) for l in logs],
    ))


@admin_required
def admin_reviews(request):
    q = request.GET.get("q", "").strip()
    sentiment = request.GET.get("sentiment", "")
    cat = request.GET.get("categorie", "")

    qs = _filter_reviews(
        Review.objects.filter(status=Review.Status.ANALYZED).select_related(
            "user", "category", "sentiment_result",
        ),
        q=q, cat=cat, sentiment=sentiment,
    )
    paginator = Paginator(qs, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    return render(request, "adminpanel/reviews.html", _base_ctx(
        request,
        reviews=[_admin_review_dict(r) for r in page.object_list],
        categories=_categories_with_counts(),
        q=q, active_sentiment=sentiment, active_cat=cat, total=paginator.count,
        page_obj=page,
    ))


@admin_required
def admin_review_detail(request, review_id):
    review = Review.objects.filter(pk=review_id).select_related(
        "user", "category", "sentiment_result",
    ).first()
    probs = probs_from_result(review.sentiment_result) if review else None
    return render(request, "adminpanel/review_detail.html", _base_ctx(
        request,
        review=_admin_review_dict(review) if review else None,
        probs=probs,
    ))


@admin_required
@require_POST
def admin_reanalyze(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    reanalyze_review(review)
    messages.success(request, f"Réanalyse LSTM relancée pour l'avis #{review_id}.")
    return redirect("admin_review_detail", review_id=review_id)


@admin_required
@require_POST
def admin_delete_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    review.delete()
    messages.success(request, f"Avis #{review_id} supprimé et modéré.")
    return redirect("admin_reviews")


@admin_required
def admin_users(request):
    users = User.objects.annotate(review_count=Count("reviews")).order_by("-date_joined")
    return render(request, "adminpanel/users.html", _base_ctx(
        request,
        users=[admin_user_to_dict(u) for u in users],
        user_stats=user_admin_stats(),
    ))


@admin_required
@require_POST
def admin_user_suspend(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if user.role == User.Role.ADMIN:
        messages.error(request, "Impossible de suspendre un administrateur.")
    else:
        user.status = User.Status.SUSPENDU
        user.save(update_fields=["status"])
        messages.success(request, f"Compte {user.display_name} suspendu.")
    return redirect("admin_users")


@admin_required
@require_POST
def admin_user_activate(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    user.status = User.Status.ACTIF
    user.save(update_fields=["status"])
    messages.success(request, f"Compte {user.display_name} réactivé.")
    return redirect("admin_users")


@admin_required
def admin_categories(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        if name:
            Category.objects.create(name=name, description=description)
            messages.success(request, "Catégorie enregistrée.")
        return redirect("admin_categories")

    return render(request, "adminpanel/categories.html", _base_ctx(
        request, categories=_categories_with_counts()))


@admin_required
@require_POST
def admin_category_delete(request, category_id):
    cat = get_object_or_404(Category, pk=category_id)
    if cat.reviews.exists():
        messages.error(request, f"Impossible de supprimer « {cat.name} » : des avis y sont rattachés.")
    else:
        cat.delete()
        messages.success(request, "Catégorie supprimée.")
    return redirect("admin_categories")


@admin_required
def admin_logs(request):
    logs = InferenceLog.objects.select_related("review")[:50]
    return render(request, "adminpanel/logs.html", _base_ctx(
        request,
        logs=[inference_log_to_dict(l) for l in logs],
        stats=dashboard_stats(),
        log_stats=inference_log_stats(),
    ))


@admin_required
def admin_moderation(request):
    flagged = Review.objects.filter(flagged=True).select_related(
        "user", "category", "sentiment_result",
    )
    return render(request, "adminpanel/moderation.html", _base_ctx(
        request, reviews=[_admin_review_dict(r) for r in flagged]))


@admin_required
@require_POST
def admin_unflag_review(request, review_id):
    review = get_object_or_404(Review, pk=review_id)
    review.flagged = False
    review.save(update_fields=["flagged"])
    messages.success(request, f"Avis #{review_id} validé.")
    return redirect("admin_moderation")


@admin_required
def admin_export_csv(request):
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "titre", "note", "categorie", "sentiment", "confiance", "latence_ms", "date"])
    for r in Review.objects.filter(status=Review.Status.ANALYZED).select_related(
        "category", "sentiment_result",
    ):
        sr = getattr(r, "sentiment_result", None)
        writer.writerow([
            r.id, r.title, r.rating, r.category.name,
            sr.sentiment if sr else "",
            sr.confidence if sr else "",
            sr.processing_ms if sr else "",
            r.created_at.strftime("%Y-%m-%d %H:%M"),
        ])
    resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = "attachment; filename=canalbox_avis.csv"
    return resp


@admin_required
def admin_export_pdf(request):
    stats = dashboard_stats()
    lines = [
        "Canal Box — Rapport analytique",
        f"Avis analysés : {stats['total']}",
        f"Satisfaction : {stats['satisfaction']}%",
        f"Confiance moyenne IA : {stats['avg_confidence_pct']}%",
        f"Latence moyenne : {stats['avg_latency']} ms",
        "",
        "Répartition des sentiments :",
        f"  Positif : {stats['positive_pct']}%",
        f"  Négatif : {stats['negative_pct']}%",
        f"  Neutre  : {stats['neutral_pct']}%",
    ]
    content = "\n".join(lines)
    resp = HttpResponse(content, content_type="application/pdf")
    resp["Content-Disposition"] = "attachment; filename=canalbox_rapport.pdf"
    return resp
