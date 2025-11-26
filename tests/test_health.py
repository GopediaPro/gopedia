import sys
import os
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.getcwd())

from src.main import app
from src.core.config import settings

client = TestClient(app)

def test_health_check():
    print("Testing /health endpoint...")
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "env": settings.APP_ENV}
    print("Health check passed!")

if __name__ == "__main__":
    test_health_check()
