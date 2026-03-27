"""
secrets.py — Load secrets from Google Secret Manager (Cloud Run) or .env (local dev).

On Cloud Run, the K_SERVICE env var is set automatically by the runtime.
When detected, any secrets not already injected via --update-secrets are
fetched from Secret Manager and written into os.environ so the rest of
the app can use os.getenv() as usual.

Locally, python-dotenv's load_dotenv() is used instead.
"""

import os
import logging

logger = logging.getLogger(__name__)

_PROJECT = "stablepayguard"

# Secrets stored in Google Secret Manager.
# DATABASE_URL is set directly as a Cloud Run env var (not in Secret Manager).
_GCP_SECRETS = [
    "SECRET_KEY",
    "ADMIN_PASSWORD",
    "SYNTH_API_KEY",
    "OPENAI_API_KEY",
    "RPC_URL",
    "PRIVATE_KEY",
    "POLICY_CONTRACT",
    "OWNER_WALLET",
]


def load_secrets():
    """Populate os.environ from the appropriate secret source."""
    if os.getenv("K_SERVICE"):
        _load_from_gcp()
    else:
        _load_from_dotenv()


def _load_from_gcp():
    """Fetch any missing secrets from Google Secret Manager."""
    try:
        from google.cloud import secretmanager
    except ImportError:
        logger.error(
            "google-cloud-secret-manager is not installed; "
            "secrets not loaded from GCP. Run: pip install google-cloud-secret-manager"
        )
        return

    client = secretmanager.SecretManagerServiceClient()
    loaded, skipped = [], []

    for name in _GCP_SECRETS:
        if os.getenv(name):
            skipped.append(name)
            continue  # already injected by --update-secrets; no need to fetch

        secret_path = f"projects/{_PROJECT}/secrets/{name}/versions/latest"
        try:
            response = client.access_secret_version(name=secret_path)
            os.environ[name] = response.payload.data.decode("utf-8")
            loaded.append(name)
        except Exception as e:
            logger.warning("Could not load secret %s from Secret Manager: %s", name, e)

    if loaded:
        logger.info("Fetched %d secret(s) from Secret Manager: %s", len(loaded), loaded)
    if skipped:
        logger.info("Skipped %d secret(s) already set by Cloud Run: %s", len(skipped), skipped)


def _load_from_dotenv():
    """Load .env file for local development."""
    from dotenv import load_dotenv
    load_dotenv()
    logger.debug("Loaded environment from .env (local dev)")
