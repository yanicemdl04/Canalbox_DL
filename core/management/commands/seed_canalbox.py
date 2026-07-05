"""Peuple la base SQLite avec les données initiales Canal Box."""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.demo_data import CATEGORIES, _AUTHORS, _TITLES
from core.models import Category, InferenceLog, Review, SentimentResult, User
from core.presenters import get_sentiment_result
from core.services.review_service import analyze_review


class Command(BaseCommand):
    help = "Insère catégories, utilisateurs, avis et résultats LSTM de démonstration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Supprime toutes les données métier avant de seed.",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Nettoyage des données existantes…")
            InferenceLog.objects.all().delete()
            SentimentResult.objects.all().delete()
            Review.objects.all().delete()
            Category.objects.all().delete()
            User.objects.all().delete()

        if Category.objects.exists():
            self.stdout.write(self.style.WARNING("Données déjà présentes — utilisez --flush pour réinitialiser."))
            return

        self._seed_categories()
        users = self._seed_users()
        self._seed_reviews(users)
        self.stdout.write(self.style.SUCCESS("Seed Canal Box terminé."))
        self.stdout.write("  Client  : yanice.client@canalbox.cd / demo1234")
        self.stdout.write("  Admin   : david.admin@canalbox.cd / demo1234")

    def _seed_categories(self):
        for cat in CATEGORIES:
            Category.objects.create(
                name=cat["name"],
                slug=cat["slug"],
                description=cat["description"],
                icon=cat["icon"],
            )
        self.stdout.write(f"  {len(CATEGORIES)} catégories créées.")

    def _seed_users(self):
        admin = User.objects.create_user(
            username="david",
            email="david.admin@canalbox.cd",
            password="demo1234",
            first_name="David",
            last_name="Débuze",
            role=User.Role.ADMIN,
            plan="Administrateur plateforme",
        )
        admin.date_joined = timezone.make_aware(datetime(2025, 1, 5))
        admin.save(update_fields=["date_joined"])

        client = User.objects.create_user(
            username="yanice",
            email="yanice.client@canalbox.cd",
            password="demo1234",
            first_name="Yanice",
            last_name="Mundele",
            role=User.Role.CLIENT,
            plan="Canal Box Fibre 200",
        )
        client.date_joined = timezone.make_aware(datetime(2025, 3, 12))
        client.save(update_fields=["date_joined"])

        extra_clients = [
            ("Joël", "Lumpungu", "joel.stone@canalbox.cd", User.Status.ACTIF, 2025, 4, 3),
            ("Junior", "Bakana", "junior.bakana@canalbox.cd", User.Status.SUSPENDU, 2025, 4, 18),
            ("Grâce", "Kabongo", "grace.kabongo@canalbox.cd", User.Status.ACTIF, 2025, 2, 27),
            ("Estelle", "Dyese", "estelle.dyese@canalbox.cd", User.Status.ACTIF, 2025, 5, 9),
        ]
        for first, last, email, status, y, m, d in extra_clients:
            u = User.objects.create_user(
                username=email.split("@")[0],
                email=email,
                password="demo1234",
                first_name=first,
                last_name=last,
                role=User.Role.CLIENT,
                status=status,
            )
            u.date_joined = timezone.make_aware(datetime(y, m, d))
            u.save(update_fields=["date_joined"])

        self.stdout.write(f"  {User.objects.count()} utilisateurs créés.")
        return list(User.objects.filter(role=User.Role.CLIENT, status=User.Status.ACTIF))

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

            # Ajuster la confiance pour coller aux données de démo si le stub diverge
            sr = get_sentiment_result(review)
            if sr:
                SentimentResult.objects.filter(pk=sr.pk).update(
                    sentiment=expected_sentiment,
                    confidence=expected_conf,
                )
                sr.refresh_from_db()

        # Log d'erreur simulé pour la démo
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
