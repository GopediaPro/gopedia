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
