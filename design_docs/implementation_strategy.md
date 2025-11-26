# Gopedia Implementation Strategy & Directory Structure

## Overview
This document outlines the step-by-step implementation strategy for **Gopedia: Headless Contextual Data Engine**. It aligns with the Hexagonal Architecture and prepares for the integration of gRPC plugins.

## Directory Structure Proposal
To align with the `README.md` and standard practices, we propose moving the source code into a `src` directory.

```
gopedia/
├── alembic/                  # Database Migrations (Auto-generated)
├── src/
│   ├── main.py               # Application Entry Point (FastAPI)
│   ├── core/                 # Core Framework
│   │   ├── config.py         # Settings & Env Vars
│   │   └── plugin/           # gRPC Plugin Adapters
│   ├── domain/               # Pure Business Logic & Entities
│   │   ├── entities.py       # SQLAlchemy Models / Data Classes
│   │   └── repositories.py   # Abstract Interfaces (Ports)
│   ├── infrastructure/       # External Implementations (Adapters)
│   │   ├── database.py       # DB Connection & Session Manager
│   │   └── repositories/     # SQLAlchemy Repository Implementations
│   ├── services/             # Application Services (Use Cases)
│   │   ├── ingestion.py      # Data Ingestion Logic
│   │   └── query.py          # Contextual Query Engine
│   └── interface/            # Primary Adapters (API)
│       ├── api/              # FastAPI Routers
│       └── grpc/             # gRPC Server (if Core acts as Server too)
├── tests/                    # Automated Tests
├── .env                      # Environment Variables
├── alembic.ini               # Alembic Config
├── requirements.txt          # Dependencies
└── README.md                 # Project Documentation
```

## Implementation Phases

### Phase 1: The Rhizome Skeleton (DB & Config)
**Goal**: Establish the persistent storage layer and configuration management.
- [ ] **Refactor**: Move `app` to `src` to match `README.md`.
- [ ] **Infrastructure**: Implement `src/infrastructure/database.py` for Async SQLAlchemy engine.
- [ ] **Migrations**: Initialize Alembic (`alembic init alembic`) and configure `env.py` to use `src.domain.entities.Base`.
- [ ] **Repository Implementation**: Implement `SqlAlchemyRhizomeRepository` in `src/infrastructure/repositories/`.

### Phase 2: gRPC Plugin Orchestrator
**Goal**: Enable communication with external microservices (Plugins).
- [ ] **Proto Definition**: Define `gopedia_plugin.proto` with generic `Execute` RPC.
- [ ] **Plugin Registry**: Create a mechanism to register/discover plugins (e.g., via `.env` or a config file).
- [ ] **Client Implementation**: Flesh out `GenericGrpcPluginClient` with actual `grpc.aio` calls.
- [ ] **Integration Test**: Create a mock gRPC server to verify the client.

### Phase 3: Contextual Query Engine
**Goal**: Implement the logic to retrieve and shape data based on context.
- [ ] **Query Service**: Create `src/services/query.py`.
- [ ] **View Resolvers**: Implement logic to transform `OriginData` into `Kanban`, `Timeline`, or `Report` views.
- [ ] **API Layer**: Create FastAPI endpoints (`GET /query`) to expose this functionality.

### Phase 4: AI & Revision Pipelines
**Goal**: Add intelligence and history tracking.
- [ ] **Revision Logic**: Implement `create_revision` in `src/services/ingestion.py`.
- [ ] **AI Plugin Integration**: Connect to an AI Plugin (via gRPC) to generate embeddings and summaries during ingestion.
- [ ] **Vector Search**: Implement `find_similar` using `pgvector` in the repository.

## Next Steps
1.  Approve this structure.
2.  Begin **Phase 1** by refactoring the directory and setting up the database connection.
