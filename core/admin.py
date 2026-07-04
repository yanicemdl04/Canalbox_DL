from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, InferenceLog, Review, SentimentResult, User


@admin.register(User)
class CanalboxUserAdmin(UserAdmin):
    list_display = ("email", "display_name", "role", "status", "plan", "is_active")
    list_filter = ("role", "status", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        ("Canal Box", {"fields": ("role", "plan", "status")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Canal Box", {"fields": ("role", "plan", "status")}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}


class SentimentResultInline(admin.StackedInline):
    model = SentimentResult
    extra = 0


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "category", "rating", "status", "flagged", "created_at")
    list_filter = ("status", "flagged", "category", "rating")
    search_fields = ("title", "content")
    inlines = [SentimentResultInline]


@admin.register(SentimentResult)
class SentimentResultAdmin(admin.ModelAdmin):
    list_display = ("review", "sentiment", "confidence", "model_version", "analyzed_at")
    list_filter = ("sentiment", "model_version")


@admin.register(InferenceLog)
class InferenceLogAdmin(admin.ModelAdmin):
    list_display = ("id", "review", "status", "sentiment", "latency_ms", "created_at")
    list_filter = ("status", "model_version")
