"""Peuple la base SQLite avec les données initiales Canal Box."""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.demo_data import CATEGORIES, DEMO_PASSWORD, DEMO_USERS, _AUTHORS, _TITLES
from core.models import Category, InferenceLog, Review, SentimentResult, User
from core.presenters import get_sentiment_result
from core.services.review_service import analyze_review

ADMIN_EMAIL = DEMO_USERS["admin"]["email"]
CLIENT_EMAIL = DEMO_USERS["client"]["email"]


class Command(BaseCommand):
    help = "Insère catégories, utilisateurs, avis et résultats LSTM de démonstration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Supprime toutes les données métier avant de seed.",
        )
        parser.add_argument(
            "--accounts-only",
            action="store_true",
            help="Catégories + comptes démo uniquement (sans avis ni inférence LSTM).",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Nettoyage des données existantes…")
            InferenceLog.objects.all().delete()
            SentimentResult.objects.all().delete()
            Review.objects.all().delete()
            Category.objects.all().delete()
            User.objects.all().delete()

        demo_ready = (
            Category.objects.exists()
            and User.objects.filter(email=ADMIN_EMAIL).exists()
            and User.objects.filter(email=CLIENT_EMAIL).exists()
        )
        if demo_ready and not options["flush"]:
            self.stdout.write(self.style.WARNING("Comptes démo déjà présents."))
        else:
            if not Category.objects.exists():
                self._seed_categories()
            self._ensure_demo_users()

        if not options["accounts_only"] and not Review.objects.exists():
            authors = list(User.objects.filter(role=User.Role.CLIENT, status=User.Status.ACTIF))
            if authors:
                self._seed_reviews(authors)

        self.stdout.write(self.style.SUCCESS("Seed Canal Box terminé."))
        self.stdout.write(f"  Client  : {CLIENT_EMAIL} / {DEMO_PASSWORD}")
        self.stdout.write(f"  Admin   : {ADMIN_EMAIL} / {DEMO_PASSWORD}")

    def _seed_categories(self):
        for cat in CATEGORIES:
            Category.objects.create(
                name=cat["name"],
                slug=cat["slug"],
                description=cat["description"],
                icon=cat["icon"],
            )
        self.stdout.write(f"  {len(CATEGORIES)} catégories créées.")

    def _ensure_demo_users(self):
        admin_data = DEMO_USERS["admin"]
        admin, created = User.objects.get_or_create(
            email=admin_data["email"],
            defaults={
                "username": "jelly",
                "first_name": "Jelly",
                "last_name": "",
                "role": User.Role.ADMIN,
                "plan": admin_data["plan"],
            },
        )
        admin.username = "jelly"
        admin.first_name = "Jelly"
        admin.last_name = ""
        admin.role = User.Role.ADMIN
        admin.plan = admin_data["plan"]
        admin.set_password(DEMO_PASSWORD)
        if created:
            admin.date_joined = timezone.make_aware(datetime(2025, 1, 5))
        admin.save()

        client_data = DEMO_USERS["client"]
        client, created = User.objects.get_or_create(
            email=client_data["email"],
            defaults={
                "username": "yanice",
                "first_name": "Yanice",
                "last_name": "Mundele",
                "role": User.Role.CLIENT,
                "plan": client_data["plan"],
            },
        )
        client.set_password(DEMO_PASSWORD)
        if created:
            client.date_joined = timezone.make_aware(datetime(2025, 3, 12))
        client.save()

        extra_clients = [
            ("Joël", "Lumpungu", "joel.stone@canalbox.cd", User.Status.ACTIF, 2025, 4, 3),
            ("Junior", "Bakana", "junior.bakana@canalbox.cd", User.Status.SUSPENDU, 2025, 4, 18),
            ("Grâce", "Kabongo", "grace.kabongo@canalbox.cd", User.Status.ACTIF, 2025, 2, 27),
            ("Estelle", "Dyese", "estelle.dyese@canalbox.cd", User.Status.ACTIF, 2025, 5, 9),
        ]
        for first, last, email, status, y, m, d in extra_clients:
            u, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],
                    "first_name": first,
                    "last_name": last,
                    "role": User.Role.CLIENT,
                    "status": status,
                },
            )
            u.set_password(DEMO_PASSWORD)
            if created:
                u.date_joined = timezone.make_aware(datetime(y, m, d))
            u.save()

        self.stdout.write(f"  {User.objects.count()} utilisateurs prêts.")

    def _seed_reviews(self, authors):
        base = timezone.now()
        flagged_indices = {1, 4, 9}
        categories = {c.slug: c for c in Category.objects.all()}

        for i, (title, content, rating, cat_id, expected_sentiment, expected_conf) in enumerate(_TITLES):
            author_name, _ = _AUTHORS[i % len(_AUTHORS)]
            author = next(
                (u for u in authors if author_name.split()[0] in u.display_name),
                authors[i % len(authors)],
            )
            cat_data = next(c for c in CATEGORIES if c["id"] == cat_id)
            category = categories[cat_data["slug"]]
            created = base - timedelta(hours=i * 7 + 3, minutes=i * 11)

            review = Review.objects.create(
                user=author,
                category=category,
                title=title,
                content=content,
                rating=rating,
                status=Review.Status.PENDING,
                flagged=i in flagged_indices,
            )
            Review.objects.filter(pk=review.pk).update(created_at=created)
            review.refresh_from_db()

            analyze_review(review)

            sr = get_sentiment_result(review)
            if sr:
                SentimentResult.objects.filter(pk=sr.pk).update(
                    sentiment=expected_sentiment,
                    confidence=expected_conf,
                )

        last_review = Review.objects.order_by("-created_at").first()
        if last_review:
            InferenceLog.objects.create(
                review=last_review,
                status=InferenceLog.Status.ERROR,
                latency_ms=3120,
                model_version="lstm-stub",
                error_message="Timeout simulé (seed)",
            )

        self.stdout.write(f"  {Review.objects.count()} avis analysés.")
