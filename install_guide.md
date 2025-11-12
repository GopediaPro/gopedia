설치 및 실행 가이드1. 환경 설정1.1. Python 가상 환경 생성Python 3.10 이상 버전을 권장합니다.# 'venv'라는 이름의 가상 환경 생성
python -m venv venv

# 가상 환경 활성화 (Windows)
.\venv\Scripts\activate

# 가상 환경 활성화 (macOS/Linux)
source venv/bin/activate
1.2. 종속성 설치requirements.txt 파일에 명시된 라이브러리들을 설치합니다.pip install -r requirements.txt
2. 데이터베이스 설정2.1. 환경 변수 설정프로젝트 루트 디렉터리에 .env 파일을 생성하고, alembic.ini 파일과 src/core/config.py에서 참조할 환경 변수를 설정합니다..env 예시:# 비동기 PostgreSQL 드라이버 (asyncpg) 사용
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/vpage_db

# Outline 서비스 API 키 (예시)
OUTLINE_API_URL=[https://api.getoutline.com](https://api.getoutline.com)
OUTLINE_API_KEY=your_api_key_here
2.2. Alembic 마이그레이션Alembic은 SQLAlchemy 모델을 기반으로 데이터베이스 스키마를 관리(생성, 변경)합니다.중요: alembic.ini 파일과 alembic/env.py 파일이 src/core/config.py의 DATABASE_URL을 올바르게 참조하고, src/models/base.py의 Base.metadata를 타겟으로 하도록 설정되어 있어야 합니다. (제공된 코드 파일에 설정됨)Alembic 초기화 (최초 1회)(이미 init_project.sh로 기본 구조를 만들었지만, 정식으로 실행하려면)alembic init alembic마이그레이션 스크립트 생성모델(src/models/models.py) 변경 사항을 감지하여 마이그레이션 스크립트를 자동 생성합니다.alembic revision --autogenerate -m "Initial migration with Anchor, VirtualPage, Revision"
데이터베이스에 마이그레이션 적용생성된 스크립트를 실제 데이터베이스에 적용합니다.alembic upgrade head
3. FastAPI 서버 실행Uvicorn을 사용하여 FastAPI 애플리케이션을 실행합니다.# src 디렉터리 내부의 main.py 파일에 있는 app 객체를 실행
# --reload 옵션은 코드 변경 시 서버를 자동 재시작합니다 (개발용)
uvicorn src.main:app --reload
서버가 실행되면 http://127.0.0.1:8000/docs 에서 Swagger UI (API 문서)를 확인할 수 있습니다.