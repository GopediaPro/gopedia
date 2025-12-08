# The Painstaker’s Guide to the encyclOpedia

## 설치 및 설정

### 1. PostgreSQL 및 pgvector 확장 설치

이 프로젝트는 PostgreSQL의 `pgvector` 확장을 사용합니다. 먼저 PostgreSQL 서버에 pgvector를 설치해야 합니다.

#### macOS (Homebrew)
```bash
# PostgreSQL이 Homebrew로 설치된 경우
brew install pgvector

# PostgreSQL 재시작
brew services restart postgresql@17  # 버전에 맞게 조정
```

#### Ubuntu/Debian
```bash
# PostgreSQL 버전에 맞는 pgvector 설치
sudo apt-get install postgresql-17-pgvector  # 버전에 맞게 조정

# PostgreSQL 재시작
sudo systemctl restart postgresql
```

#### Docker 사용 시
```bash
# pgvector가 포함된 PostgreSQL 이미지 사용
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=yourpassword \
  -p 5432:5432 \
  pgvector/pgvector:pg17
```

#### 소스에서 빌드
[pgvector 설치 가이드](https://github.com/pgvector/pgvector#installation) 참조

**중요**: pgvector 설치 후 PostgreSQL 서버를 재시작해야 합니다.

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# library 설치
python3 -m pip install -r requirements.txt

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

## GitHub Mock Data Seeding

GitHub 리포지토리의 파일 정보를 가져와서 데이터베이스에 mock data를 생성할 수 있습니다.

### 1. 환경 변수 설정

`.env` 파일에 GitHub 관련 설정을 추가합니다:

```bash
# GitHub API Configuration
GITHUB_OWNER=octocat          # 리포지토리 소유자
GITHUB_REPO=Hello-World       # 리포지토리 이름
GITHUB_BRANCH=main            # 브랜치 이름 (기본값: main)
GITHUB_TOKEN=                 # 선택사항: GitHub Personal Access Token (rate limit 증가용)
```

GitHub Token은 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)에서 생성할 수 있습니다.

### 2. Mock Data 생성

```bash
# .env 파일의 설정값 사용
python scripts/seed_github_mock_data.py

# 명령줄 인자로 특정 값 오버라이드
python scripts/seed_github_mock_data.py --owner octocat --repo Hello-World

# 특정 브랜치 지정
python scripts/seed_github_mock_data.py --branch develop

# GitHub Token 사용
python scripts/seed_github_mock_data.py --token <your_token>
```

### 3. 생성되는 데이터

스크립트는 다음 데이터를 생성합니다:
- **SysDict**: SOURCE, DTYPE, PRED, TAG, EDITOR 카테고리
- **OriginData**: 리포지토리 및 파일의 고유 식별자 (URN 형식)
- **TreeNode**: 폴더 구조 및 파일 위치
- **BlobStore**: 파일 내용 (SHA-256 해시 기반 중복 제거)
- **Revision**: 문서 버전 정보
- **ChunkNode**: 텍스트 파일의 청크 (검색 최적화)
- **KnowledgeEdge**: 리포지토리-파일 관계
