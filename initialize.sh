#!/bin/bash

echo "🌱 Initializing Gopedia Project Structure..."

# 1. Create Directory Hierarchy
mkdir -p app
mkdir -p core/db
mkdir -p core/plugin
mkdir -p domain/entities
mkdir -p domain/schemas
mkdir -p domain/repository
mkdir -p migrations/versions
mkdir -p proto
mkdir -p core/plugin/generated # gRPC Generated Code (Auto)
mkdir .github
mkdir .github/workflows
mkdir .github/ISSUE_TEMPLATE

#  2. Create files
touch main.py
touch app/config.py
touch core/db/session.py
touch core/plugin/interface.py
touch domain/entities/base.py
touch domain/entities/models.py
touch domain/schemas/plugin.py
touch domain/repositories.py
touch migrations/env.py
touch proto/gopedia.proto # .proto 정의 파일
touch core/plugin/client.py # gRPC Adapter Implementation
touch core/plugin/registry.py # Plugin Manager
touch .github/PULL_REQUEST_TEMPLATE.md
touch .github/workflows/create_issue_branch.yml
touch .github/ISSUE_TEMPLATE/custom_issue.yml

# 3. Create __init__.py for packages
touch app/__init__.py
touch core/__init__.py core/db/__init__.py core/plugin/__init__.py
touch domain/__init__.py domain/entities/__init__.py domain/schemas/__init__.py
touch proto/__init__.py
touch core/plugin/generated/__init__.py


# 4. Create .env (Configuration)
cat > .env <<EOF
# Application
APP_NAME="Gopedia Engine"
DEBUG=True
SECRET_KEY="dev_secret_key_change_in_prod"

# Database (Docker Default)
# Driver: postgresql+asyncpg
DATABASE_URL="postgresql+asyncpg://gopedia:gopedia_pass@localhost:5432/gopedia_db"

# Plugin Registry (Mock for now)
PLUGIN_REGISTRY="{}"
EOF

# 5. Create .gitignore
cat > .gitignore <<EOF
__pycache__/
*.py[cod]
.env
.venv/
env/
.idea/
.vscode/
*.log
postgres_data/
EOF

echo "✅ Project structure created successfully!"
echo "   Next: Run 'pip install -r requirements.txt'"