#!/bin/bash

# 프로젝트 루트 디렉터리 생성 (이미 있다면 생략)
# mkdir virtual-page-service
# cd virtual-page-service

# 기본 디렉터리 구조 생성
mkdir -p src/controllers
mkdir -p src/services
mkdir -p src/repositories
mkdir -p src/models
mkdir -p src/schemas
mkdir -p src/core
mkdir -p alembic/versions

# __init__.py 파일 생성 (Python 패키지 인식용)
touch src/__init__.py
touch src/controllers/__init__.py
touch src/services/__init__.py
touch src/repositories/__init__.py
touch src/models/__init__.py
touch src/schemas/__init__.py
touch src/core/__init__.py
touch alembic/__init__.py

# 빈 파일 생성 (나중에 채울 파일들)
touch src/main.py
touch src/controllers/source_controller.py
touch src/controllers/publish_controller.py
touch src/controllers/virtual_page_controller.py
touch src/services/base_source_service.py
touch src/services/github_service.py
touch src/services/outline_service.py
touch src/repositories/base_repository.py
touch src/repositories/virtual_page_repository.py
touch src/models/base.py
touch src/models/models.py
touch src/schemas/anchor_schema.py
touch src/schemas/virtual_page_schema.py
touch src/schemas/source_schema.py
touch src/schemas/publish_schema.py
touch src/core/config.py
touch src/core/database.py

touch .env
touch .gitignore
touch requirements.txt
touch README.md
touch install_guide.md

# Alembic 기본 파일 생성 (이 부분은 'alembic init alembic' 명령으로 대체하는 것이 좋습니다)
# 여기서는 요청된 구조에 맞게 수동으로 생성합니다.
touch alembic/env.py
touch alembic/script.py.mako
touch alembic.ini # 이 파일은 alembic init으로 생성해야 함

echo "프로젝트 구조 생성이 완료되었습니다."
echo "주의: 'alembic.ini' 파일은 'alembic init alembic' 명령을 실행하여 생성하거나 수동으로 구성해야 합니다."