import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# .env 파일 로드 (alembic env.py와 중복될 수 있으나, FastAPI 실행 시 필요)
# 프로젝트 루트에 .env가 있다고 가정
load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str
    
    OUTLINE_API_URL: str = "https://api.getoutline.com"
    OUTLINE_API_KEY: str
    
    GITHUB_API_TOKEN: str | None = None

    class Config:
        # .env 파일 대신 환경 변수에서 직접 읽도록 설정할 수도 있음
        env_file = ".env" 
        env_file_encoding = 'utf-8'

# 설정 객체 인스턴스화 (다른 모듈에서 임포트하여 사용)
settings = Settings()