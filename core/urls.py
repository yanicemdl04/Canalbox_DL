from django.urls import path

from . import views

urlpatterns = [
    # Public
    path("", views.landing, name="landing"),
    path("connexion/", views.login_view, name="login"),
    path("inscription/", views.register_view, name="register"),
    path("mot-de-passe-oublie/", views.forgot_password_view, name="forgot_password"),
    path("deconnexion/", views.logout_view, name="logout"),

    # Client
    path("espace/", views.client_dashboard, name="client_dashboard"),
    path("espace/avis/", views.client_reviews, name="client_reviews"),
    path("espace/avis/nouveau/", views.client_review_create, name="client_review_create"),
    path("espace/avis/<int:review_id>/", views.client_review_detail, name="client_review_detail"),
    path("espace/profil/", views.client_profile, name="client_profile"),
    path("espace/profil/modifier/", views.client_profile_edit, name="client_profile_edit"),

    # Administrateur
    path("administration/", views.admin_dashboard, name="admin_dashboard"),
    path("administration/avis/", views.admin_reviews, name="admin_reviews"),
    path("administration/avis/<int:review_id>/", views.admin_review_detail, name="admin_review_detail"),
    path("administration/avis/<int:review_id>/reanalyser/", views.admin_reanalyze, name="admin_reanalyze"),
    path("administration/avis/<int:review_id>/supprimer/", views.admin_delete_review, name="admin_delete_review"),
    path("administration/utilisateurs/", views.admin_users, name="admin_users"),
    path("administration/categories/", views.admin_categories, name="admin_categories"),
    path("administration/logs/", views.admin_logs, name="admin_logs"),
    path("administration/moderation/", views.admin_moderation, name="admin_moderation"),
    path("administration/exports/csv/", views.admin_export_csv, name="admin_export_csv"),
    path("administration/exports/pdf/", views.admin_export_pdf, name="admin_export_pdf"),
]
