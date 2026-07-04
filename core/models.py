from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify


class User(AbstractUser):
    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        ADMIN = "admin", "Administrateur"

    class Status(models.TextChoices):
        ACTIF = "actif", "Actif"
        SUSPENDU = "suspendu", "Suspendu"

    email = models.EmailField("adresse e-mail", unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CLIENT)
    plan = models.CharField(max_length=120, default="Canal Box Fibre 200")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIF)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        ordering = ["-date_joined"]

    @property
    def display_name(self):
        full = self.get_full_name().strip()
        return full or self.email.split("@")[0]

    @property
    def initials(self):
        parts = self.display_name.split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        return self.display_name[:2].upper()

    @property
    def member_since(self):
        months = [
            "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
            "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
        ]
        return f"{months[self.date_joined.month - 1]} {self.date_joined.year}"

    @property
    def avatar_color(self):
        if self.role == self.Role.ADMIN:
            return "from-neutral-800 to-neutral-600"
        return "from-pink-500 to-rose-400"


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=20, default="folder")

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "categorie"
            slug = base
            n = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)


class Review(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "En attente d'analyse"
        ANALYZED = "analyzed", "Analysé"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="reviews")
    title = models.CharField(max_length=200)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    flagged = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SentimentResult(models.Model):
    class Sentiment(models.TextChoices):
        POSITIF = "positif", "Positif"
        NEGATIF = "negatif", "Négatif"
        NEUTRE = "neutre", "Neutre"

    review = models.OneToOneField(Review, on_delete=models.CASCADE, related_name="sentiment_result")
    sentiment = models.CharField(max_length=10, choices=Sentiment.choices)
    confidence = models.FloatField()
    prob_positif = models.FloatField(default=0)
    prob_negatif = models.FloatField(default=0)
    prob_neutre = models.FloatField(default=0)
    processing_ms = models.PositiveIntegerField(default=0)
    model_version = models.CharField(max_length=50, default="lstm-stub")
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-analyzed_at"]


class InferenceLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "succès", "Succès"
        ERROR = "erreur", "Erreur"

    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="inference_logs")
    status = models.CharField(max_length=10, choices=Status.choices)
    sentiment = models.CharField(max_length=10, blank=True, default="")
    confidence = models.FloatField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(default=0)
    model_version = models.CharField(max_length=50, default="lstm-stub")
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
