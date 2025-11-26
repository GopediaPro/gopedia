from fastapi import FastAPI
from src.core.config import settings

app = FastAPI(
    title="Gopedia: Headless Contextual Data Engine",
    version="0.1.0",
    description="Headless backend for Gopedia.",
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
