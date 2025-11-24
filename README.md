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

# library 설치
pip3 install -r requirements.txt

# 8011 포트 fastAPI 실행
uvicorn src.main:app --port 8011 --reload

# DB migration
alembic revision --autogenerate -m "Initial migration"
```

## Alembic (DB 마이그레이션) 적용 및 사용법

### 1. Alembic 설치

```bash
pip install alembic
```

### 2. Alembic 환경설정
- alembic.ini의 DB URL은 비워두고, alembic/env.py에서 환경변수 또는 settings를 통해 동적으로 DB URL을 주입합니다.
- alembic/env.py에서 모든 모델이 Base.metadata에 등록되도록 `import models`를 반드시 추가합니다.
- 마이그레이션 파일(예: alembic/versions/...)은 반드시 git에 커밋합니다.

### 3. Alembic 기본 명령어

```bash
# 마이그레이션 파일 생성 (모델 변경 후)
alembic revision --autogenerate -m "설명 메시지"

# DB에 마이그레이션 적용
alembic upgrade head

# DB를 특정 리비전으로 되돌리기 (주의: 데이터 손실 가능)
alembic downgrade <revision_id>

# DB와 마이그레이션 버전 동기화만 (실제 구조 변경 X, 운영 DB에 적용 시)
alembic stamp head
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
gopedia/
├── app/
│   ├── config.py           # Pydantic Settings
│   └── main.py             # Entry point
├── core/
│   ├── db/                 # Database Session Manager
│   └── plugin/             # gRPC Adapter Implementations
├── domain/
│   ├── entities/           # SQLAlchemy Models (Core Logic)
│   ├── schemas/            # Pydantic DTOs (Validation)
│   └── repositories.py     # Abstract Interfaces
└── migrations/             # Alembic scripts
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

## TEST
```bash
# pytest로 실행
pytest tests/test_connections.py -v

# 또는 직접 실행
python tests/test_connections.py
```