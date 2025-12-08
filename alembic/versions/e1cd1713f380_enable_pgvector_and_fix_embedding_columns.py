"""251208_0.0.3_enable pgvector and fix embedding columns

Revision ID: e1cd1713f380
Revises: 9897aa580db9
Create Date: 2025-12-08 01:04:24.746576

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1cd1713f380'
down_revision: Union[str, Sequence[str], None] = '9897aa580db9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.
    
    IMPORTANT: Before running this migration, ensure pgvector is installed on your PostgreSQL server
    and the vector extension is created (requires superuser privileges):
    
        CREATE EXTENSION IF NOT EXISTS vector;
    
    Installation instructions:
    - macOS (Homebrew): brew install pgvector && brew services restart postgresql@<version>
    - Ubuntu/Debian: apt-get install postgresql-<version>-pgvector && systemctl restart postgresql
    - Docker: Use pgvector/pgvector:pg<version> image
    - From source: https://github.com/pgvector/pgvector#installation
    
    NOTE: This migration assumes the vector extension is already created.
    If you get "type vector does not exist", create the extension first as a superuser.
    """
    # Note: Extension creation is skipped here because it requires superuser privileges.
    # The extension should be created manually before running this migration:
    #   CREATE EXTENSION IF NOT EXISTS vector;
    
    # Alter embedding columns from TEXT to vector(1536)
    # Note: This will set all existing values to NULL since we can't directly convert TEXT to vector
    # If you have important embedding data stored as TEXT, you'll need to handle it separately
    # by exporting the data, converting it, and re-importing it
    op.execute('ALTER TABLE revisions ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536)')
    op.execute('ALTER TABLE chunk_nodes ALTER COLUMN embedding TYPE vector(1536) USING NULL::vector(1536)')


def downgrade() -> None:
    """Downgrade schema."""
    # Convert vector columns back to TEXT
    op.execute('ALTER TABLE chunk_nodes ALTER COLUMN embedding TYPE TEXT USING NULL')
    op.execute('ALTER TABLE revisions ALTER COLUMN embedding TYPE TEXT USING NULL')
    
    # Drop pgvector extension (optional - comment out if you want to keep it)
    # op.execute('DROP EXTENSION IF EXISTS vector')
