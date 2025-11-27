"""
Fast settings for running tests locally with a short runtime.

This file imports the project's normal settings and overrides a few
settings for speed:
- in-memory SQLite database (faster to create/tear down)
- disable migrations (creates tables directly from models)
- use fast password hasher (MD5) so creating users is quick
- use console/dummy email backend

Usage: set environment variable FAST_TESTS=1 and the test runners
in this repo will switch to this settings module.
"""
from .settings import *  # noqa: F401,F403

# Database: use in-memory SQLite for fastest test DB
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Avoid running migrations (Django will create tables directly) — this
# speeds up setup significantly for tests that don't rely on custom
# migration operations.
class DisableMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Make password hashing extremely fast in tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use console mail backend — avoids network calls and makes tests deterministic
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Keep timezone settings but reduce overhead where possible
USE_TZ = False

# Recommended: reduce logging noise
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
