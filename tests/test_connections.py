import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure required settings exist before importing the FastAPI app
os.environ.setdefault("APP_NAME", "Gopedia Engine")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://gopedia:gopedia_pass@localhost:5432/gopedia_db",
)
os.environ.setdefault("PLUGIN_REGISTRY", "{}")

from fastapi.testclient import TestClient  # noqa: E402
from main import app  # noqa: E402


def test_health_endpoint_returns_ok():
    """FastAPI health endpoint should respond without raising plugin errors."""
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert isinstance(payload.get("plugins_active"), list)

