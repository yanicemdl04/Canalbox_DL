"""Project middleware helpers.

This module is NOT used by Django directly.

Django uses the `MIDDLEWARE` list from `canalbox/settings.py`.

However, some deployments (or earlier project iterations) may expect
static files settings to live here. To support Render deployment with
WhiteNoise, we keep the canonical static files configuration here as
well.

If you are editing for production, prefer updating
`Canalbox_DL/canalbox/settings.py`.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Kept for backward compatibility (do not use as Django setting source).
# Note: Django will ignore this if not referenced from settings.py.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

STATIC_URL = "/static/"

# Used by WhiteNoise when collecting static files.
STATIC_ROOT = BASE_DIR / "staticfiles"

# Safe for production: uses hashed filenames and raises errors if
# referenced static files are missing.
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

