# The Painstaker’s Guide to the encyclOpedia

## 설치 및 설정

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

# 가상 페이지 서비스 (Virtual Page Service) - MVP

Python의 FastAPI, SQLAlchemy (Async), Pydantic, Alembic을 사용한 가상 페이지 서비스의 1단계(MVP) 구현입니다.

## 1. 프로젝트 목표

이 프로젝트는 다양한 소스(예: GitHub)의 콘텐츠를 "Anchor"로 참조하고, 이를 기반으로 "VirtualPage"라는 가상 문서를 생성 및 관리하는 것을 목표로 합니다. MVP 단계에서는 GitHub 스캔을 통한 데이터 생성과 Outline 서비스로의 발행(Publish) 기능에 중점을 둡니다.

## 2. 기술 스택

- **Web Framework**: FastAPI
    
- **ORM**: SQLAlchemy (Asyncio 기반)
    
- **Database**: PostgreSQL (Asyncpg 드라이버)
    
- **Schema Validation**: Pydantic
    
- **Database Migrations**: Alembic
    
- **Async HTTP Client**: httpx
    
- **Configuration**: python-dotenv, Pydantic `BaseSettings`
    

## 3. 프로젝트 구조

```
/src
|-- /controllers  # API Endpoints (FastAPI Routers)
|-- /services     # Business Logic
|-- /repositories # Database Access (CRUD)
|-- /models       # SQLAlchemy Models
|-- /schemas      # Pydantic Schemas
|-- /core         # Configuration and core utilities
|-- main.py       # FastAPI App entrypoint
|
/alembic          # Alembic migration files
|-- /versions
|-- env.py
|-- script.py.mako
|
.env              # 환경 변수
.gitignore        # Git 무시 파일
requirements.txt  # Python 종속성
README.md         # 프로젝트 개요
install_guide.md  # 설치 및 실행 가이드
```

## 4. API 엔드포인트 (MVP)

- `POST /sources/github/scan`: GitHub 리포지토리를 스캔하여 Anchor와 VirtualPage를 생성합니다.
    
- `POST /publish/outline`: 특정 VirtualPage를 Outline 서비스에 발행합니다.
    
- `GET /virtual-pages/{page_id}`: VirtualPage 상세 정보를 조회합니다.
    
- `GET /anchors/by-locator`: `locator` 문자열을 기반으로 Anchor 정보를 조회합니다.