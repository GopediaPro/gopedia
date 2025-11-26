# GitHub Plugin & Sample Data Design

## Overview
This document outlines the design for the **GitHub Plugin** and the data mapping strategy to represent a GitHub source code tree within the **Rhizome Engine** (Gopedia's core).

## 1. Data Modeling (Rhizome Mapping)

We will map GitHub concepts to Rhizome entities (`OriginData`, `Revision`, `KnowledgeEdge`, `SysDict`).

### 1.1. System Dictionary (`SysDict`)
We need to bootstrap the following definitions:

*   **Source System**: `GITHUB`
*   **Data Types**:
    *   `REPOSITORY`
    *   `DIRECTORY`
    *   `FILE`
    *   `COMMIT`
    *   `USER` (Author/Committer)
*   **Predicates (Edges)**:
    *   `CONTAINS` (Repo -> Dir, Dir -> File)
    *   `AUTHORED_BY` (Commit -> User)
    *   `MODIFIED_BY` (Revision -> User)
    *   `PARENT_OF` (Commit -> Commit)
    *   `REFERENCES` (Commit -> Tree/File)

### 1.2. Entity Mapping

#### Repository
*   **Entity**: `OriginData`
*   **URN**: `github:{owner}/{repo}` (e.g., `github:octocat/Hello-World`)
*   **Type**: `REPOSITORY`
*   **Props**: `{ "description": "...", "stars": 120, "language": "Python" }`

#### Directory / File
*   **Entity**: `OriginData`
*   **URN**: `github:{owner}/{repo}:{path}` (e.g., `github:octocat/Hello-World:src/main.py`)
*   **Type**: `DIRECTORY` or `FILE`
*   **Props**: `{ "name": "main.py", "extension": "py" }`

#### Commit
*   **Entity**: `OriginData`
*   **URN**: `github:{owner}/{repo}:commit:{sha}`
*   **Type**: `COMMIT`
*   **Props**: `{ "message": "Initial commit", "date": "2023-10-27T..." }`

#### Revisions (Content Versioning)
*   **Entity**: `Revision`
*   **Linked to**: `OriginData` (File)
*   **Summary Hash**: Points to `BlobStore` containing the file content at that point in time.
*   **Meta Diff**: `{ "lines_added": 10, "lines_removed": 2 }`

### 1.3. Graph Connections (`KnowledgeEdge`)

*   `Repository` --`CONTAINS`--> `Directory` (Root)
*   `Directory` --`CONTAINS`--> `File`
*   `Directory` --`CONTAINS`--> `Directory` (Subdir)
*   `Commit` --`AUTHORED_BY`--> `User`
*   `Commit` --`PARENT_OF`--> `Commit`

## 2. Plugin Architecture

The GitHub Plugin will act as an **Ingestion Agent**.

### 2.1. Interface
It implements the `PluginClientInterface` (or exposes an API that the Generic Client consumes).

**Request (Ingest Repo):**
```json
{
  "action": "ingest",
  "payload": {
    "target": "https://github.com/octocat/Hello-World",
    "depth": "full"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "nodes_created": 15,
    "edges_created": 14,
    "root_urn": "github:octocat/Hello-World"
  }
}
```

### 2.2. Logic Flow
1.  **Fetch**: Use GitHub API (or `git clone`) to traverse the tree.
2.  **Map**: Convert each node (Dir/File) to `OriginData`.
3.  **Store**:
    *   Check if `OriginData` exists (by URN).
    *   If new, create it.
    *   Create `Revision` for the current state.
    *   Store content in `BlobStore`.
    *   Create `KnowledgeEdge` relations.

## 3. Sample Data Generation (Script)

We will create a script `scripts/seed_github_sample.py` to populate the DB with a mock "Hello World" repo structure without needing actual GitHub API access for the demo.

### Mock Structure
```
gopedia-demo/ (Repo)
├── README.md (File)
├── src/ (Dir)
│   ├── main.py (File)
│   └── utils.py (File)
└── requirements.txt (File)
```
