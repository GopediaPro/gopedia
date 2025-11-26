Implementation Plan - GitHub Sample Data Seeding
Goal
Create a script to seed the Gopedia database with a mock GitHub repository structure ("Hello World") to demonstrate the Rhizome engine's capabilities without needing live API access.

User Review Required
NOTE

This script assumes the database schema is already initialized (via Alembic).

Proposed Changes
Scripts
[NEW] 
seed_github_sample.py
A standalone Python script to:
Connect to the database.
Ensure SysDict entries exist for GitHub, Repository, File, etc.
Create OriginData nodes for a sample repo structure.
Create KnowledgeEdge connections between them.
Create Revision and BlobStore entries for file content.
Verification Plan
Automated Tests
Run the script and verify no errors:
python scripts/seed_github_sample.py
Verify data in DB (using a simple query script or manual inspection if possible).