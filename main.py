from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.plugin.registry import PluginRegistry

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 플러그인 연결
    print("🚀 Initializing Plugin Registry...")
    await PluginRegistry.initialize()
    yield
    # Shutdown: 연결 해제
    print("🛑 Shutting down Plugin Connections...")
    await PluginRegistry.shutdown()

app = FastAPI(
    title="Gopedia Headless Engine",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "plugins_active": list(PluginRegistry._clients.keys())}