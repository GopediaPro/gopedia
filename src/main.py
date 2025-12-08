from fastapi import FastAPI
from src.core.config import settings
from src.controllers.github_seed_controller import router as github_seed_router

app = FastAPI(
    title="Gopedia: Headless Contextual Data Engine",
    version="0.1.0",
    description="Headless backend for Gopedia.",
)

# Register routers
app.include_router(github_seed_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.APP_ENV}
