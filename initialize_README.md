### 🛠️ Phase 1: Implementation Checklist

1.  **Project Scaffolding:** 폴더 구조 생성 및 환경 설정 파일(`init_project.sh`)
2.  **Infrastructure:** `docker-compose.yml` (PostgreSQL + pgvector)
3.  **Dependencies:** `requirements.txt`
4.  **DB Session Manager:** `core/db/session.py` (Async Engine)
5.  **Migration Engine:** Alembic Async Setup

-----

### 1\. Project Scaffolding (자동화 스크립트)

-----

### 2\. Infrastructure (`docker-compose.yml`)

`pgvector` 확장이 이미 설치된 공식 이미지를 사용하여 설정의 번거로움을 줄입니다.

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: pgvector/pgvector:pg16
    container_name: gopedia_rhizome
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: gopedia
      POSTGRES_PASSWORD: gopedia_pass
      POSTGRES_DB: gopedia_db
    volumes:
      - ./postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gopedia -d gopedia_db"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: always

  # 추후 Redis, Plugin Service 등이 이곳에 추가됩니다.
```

-----

### 3\. Dependencies (`requirements.txt`)

-----

### 4\. DB Session Manager (`core/db/session.py`)

-----

### 5\. Alembic Migration Setup

이 부분이 가장 중요합니다. 비동기(Async) 환경에 맞춰 Alembic을 초기화하고 설정해야 합니다.

#### Step 5.1: Alembic 초기화

터미널에서 다음 명령어를 실행하여 비동기 템플릿으로 초기화합니다.

```bash
alembic init -t async migrations
```

#### Step 5.2: `migrations/env.py` 수정

Alembic이 우리의 \*\*SQLAlchemy Model(Metadata)\*\*을 인식하고, DB 설정을 `.env`에서 읽어오도록 수정해야 합니다. 자동 생성된 파일을 아래 내용으로 덮어쓰세요.

**File:** `migrations/env.py`

-----

### 🚀 Execution & Verification (실행 및 검증)

이제 모든 준비가 되었습니다. 아래 순서대로 실행하여 시스템을 기동하십시오.

1.  **스크립트 실행:** `./init_project.sh`
2.  **패키지 설치:** `pip install -r requirements.txt`
      * (이전 Task 1의 코드를 `app/config.py`, `domain/entities/` 등에 적절히 붙여넣으셔야 합니다.)
3.  **Docker 실행:** `docker-compose up -d`
4.  **초기 마이그레이션 생성:**
    ```bash
    # 모델 변경 사항 감지 및 마이그레이션 파일 생성
    alembic revision --autogenerate -m "init_rhizome_schema"
    ```
5.  **DB 반영:**
    ```bash
    alembic upgrade head
    ```

# Protobuf 컴파일
python -m grpc_tools.protoc -I./proto \
  --python_out=./core/plugin/generated \
  --grpc_python_out=./core/plugin/generated \
  --pyi_out=./core/plugin/generated \
  ./proto/gopedia.proto

**Next Step Recommendation:**
위 과정이 완료되면 DB에는 Task 1에서 설계한 `origin_data`, `sys_dict` 등의 테이블이 생성되어 있을 것입니다.

다음은 **Task 2, Phase 2: gRPC Plugin Orchestrator** 구축입니다.
Core 시스템이 외부와 소통할 수 있도록 **Proto 파일 정의와 Plugin Registry 구현**을 진행해 드릴까요?