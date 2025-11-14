from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.core.database import engine, AsyncSessionLocal
from src.models.base import Base # SQLAlchemy Base
from src.controllers import source_controller, publish_controller, virtual_page_controller

# (선택) 비동기 DB 엔진 라이프사이클 관리
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 애플리케이션 시작 시
    print("Starting up...")
    # (선택) DB 연결 테스트 또는 초기화
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all) # 개발 시 (Alembic 권장)
    yield
    # 애플리케이션 종료 시
    print("Shutting down...")
    await engine.dispose() # 엔진 연결 풀 닫기

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="가상 페이지 서비스 (Virtual Page Service)",
    description="GitHub 스캔 및 Outline 발행 MVP",
    version="0.1.0",
    lifespan=lifespan # 라이프사이클 이벤트 핸들러 등록
)

# --- 라우터 포함 ---
app.include_router(source_controller.router)
app.include_router(publish_controller.router)
app.include_router(virtual_page_controller.router)

# --- 루트 엔드포인트 ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Virtual Page Service API"}

# (선택) CORS 설정
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"], # 실제 운영 시에는 특정 도메인만 허용
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )