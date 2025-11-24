# Copilot / AI agent instructions — Local Deployment repo

**Purpose**: Help AI coding assistants become productive immediately in this repository by describing the architecture, common workflows, conventions, and key integration points discovered in the codebase.

## Big picture
- Two supported topologies:
  - Monolith demo: `docker-compose.yml` runs a React frontend (3000), FastAPI backend (8000) and MinIO (9001).
  - Microservices: `microservices/` contains an API gateway and separate services (user, document, analysis, analytics, storage). Each service follows a Clean Architecture (`domain/`, `application/`, `infrastructure/`).

## High-priority files to read
- `README.md`, `architecture.md`, `microservices/README.md` — start here for architecture and run instructions.
- `backend/`: `app.py`, `config.py`, `llm_integration.py`, `background_tasks.py`, `auth.py`, `schemas.py`, `models.py`.
- `frontend/src/`: `services/api.ts`, `pages/`, and `components/` for UI → API flow.
- `microservices/`: per-service `app.py`, `main.py`, and `Dockerfile` for independent deployments.

## Concrete dev workflows (copy-paste)
- Run monolith demo (repo root):
  - `docker-compose up -d`
  - `docker-compose logs -f`
- Frontend local dev:
  - `cd frontend && npm install && npm start`
  - Tests: `cd frontend && npm test`
- Backend local dev (no containers):
  - `cd backend && pip install -r requirements.txt && python app.py`
- Microservices (build & deploy script):
  - `chmod +x microservices/build-and-deploy.sh && ./microservices/build-and-deploy.sh`

## Key integration points & envs
- LLM: `LLM_MODE` (`mock` | `openai`). OpenAI enabled when `OPENAI_API_KEY` set. See `backend/llm_integration.py` and `microservices/llm-service`.
- Storage: MinIO (S3-compatible). Config and `STORAGE_PATH` live in `backend/config.py`, data persisted to `./data` via `docker-compose`.
- Auth: JWT tokens — see `backend/auth.py` and `microservices/*/infrastructure/auth.py`.

## Repo conventions and patterns
- Monolith-as-demo: use `docker-compose` to validate runtime changes across frontend/backend/minio.
- Microservices: implement new service with `domain/`, `application/`, `infrastructure/` and add to `microservices/docker-compose.yml` and gateway routes.
- Add API route (monolith):
  1. Add route in `backend/app.py`.
  2. Add request/response schema in `backend/schemas.py`.
  3. Update `backend/models.py` if persistence is required and helpers in `backend/utils.py`.
  4. Update `frontend/src/services/api.ts` and the UI page/component.

## Safe-edit notes
- Review `backend/config.py`, `backend/background_tasks.py`, and `backend/llm_integration.py` before making cross-cutting changes.
- Preserve `LLM_MODE=mock` for offline testing when editing prompts.
- Confirm MinIO settings when modifying storage paths — do not assume S3 in CI/local.

## Examples & troubleshooting pointers
- Health endpoints: monolith/gateway typically `http://localhost:8000/health`; microservices ports are documented in `microservices/README.md`.
- Debugging background tasks: tail backend logs (`docker-compose logs -f`) and inspect `backend/background_tasks.py`.

## Practical PR checklist
- If API changed: update `frontend/src/services/api.ts` and corresponding UI pages.
- If DB model changed: update service DB init scripts or migrations in the affected microservice.
- Keep mock LLM behavior intact for tests/CI unless explicitly changing LLM logic.

If you'd like, I can expand any of these sections (ports table, PR checklist, or a step-by-step add-route example). Ask which area to deepen.

**Big Picture**: The project provides two related topologies:
- **Local monolith for demo**: `docker-compose.yml` starts a React frontend (port 3000), a FastAPI backend (port 8000), and MinIO (port 9001). See `README.md` and `architecture.md` for diagrams and data flow.
- **Microservices variant**: `microservices/` contains an independent microservices layout (API gateway + user, document, analysis, analytics, storage services). Each service follows Clean Architecture (`domain/`, `application/`, `infrastructure/`). See `microservices/README.md`.

**Key files / places to read (high priority)**
- **`README.md`**: quick start, env vars, architecture summary, default credentials.
- **`architecture.md`**: component diagram, data flow, and local-vs-cloud differences.
- **`microservices/README.md`**: detailed microservices boundaries, ports, health endpoints and deploy scripts.
- **`backend/`**: monolithic FastAPI implementation — read `backend/app.py`, `backend/config.py`, `backend/llm_integration.py`, and `backend/background_tasks.py` to understand request handling and async processing.
- **`frontend/src/`**: React + TypeScript UI; main components live under `components/` and `pages/`.
- **`docker-compose.yml` & `docker-compose.lmstudio.yml`**: local orchestration and alternate compose configs.

**Architecture notes agents must know**
- The local demo intentionally collapses multiple microservices into a single FastAPI backend (`backend/`) for simplicity; however the repo also contains a true microservices layout under `microservices/` implementing the API Gateway pattern.
- Storage: MinIO is used as S3-compatible storage; uploaded documents and exports persist to `./data` (mounted volumes in compose).
- LLM usage: LLM integration is configurable via env `LLM_MODE` (`mock` or `openai`) and the codepaths live in `backend/llm_integration.py` (monolith) and service-level equivalents in `microservices/*/`.

**Developer workflows (concrete commands)**
- Start local demo (recommended for quick iteration):
  - `docker-compose up -d` (run from repo root)
  - `docker-compose logs -f` to follow logs
- Run microservices variant:
  - `chmod +x microservices/build-and-deploy.sh && ./microservices/build-and-deploy.sh`
- Frontend local dev / build:
  - `cd frontend && npm install` then `npm start` (dev) or `npm run build` (production bundle used by compose)
- Backend local dev (no containers):
  - `cd backend && pip install -r requirements.txt && python app.py`
- Health checks (useful for integration tests):
  - Gateway: `http://localhost:8000/health`
  - Services: `http://localhost:8001/health` .. `:8005/health` (see `microservices/README.md`)

**Conventions & patterns specific to this repo**
- Monolith vs microservices: prefer reading the monolith code under `backend/` to understand runtime behaviour when `docker-compose.yml` is used — the microservices tree follows the same domain/use-case split but scattered by service.
- Clean Architecture in `microservices/`: each service is organized as `domain/`, `application/`, `infrastructure/`. New services should follow this pattern.
- Auth: JWT tokens are used across the stack; `backend/auth.py` and microservice `infrastructure/auth.py` implement token handling and role checks.
- Data ownership: each service owns its DB and storage — avoid changing another service's data layer directly; use service APIs for cross-service interaction.

**Integration points and external dependencies**
- MinIO (S3-compatible) — see `docker-compose.yml` mounts and the `STORAGE_PATH`/MinIO client created in `backend/config.py`.
- OpenAI: enabled when `LLM_MODE=openai` and `OPENAI_API_KEY` set. Mock mode (`LLM_MODE=mock`) simulates LLM responses (useful for offline testing).
- Docker: primary orchestration for demo; microservices can be run individually for development.

**When editing code, pay attention to these files for cross-cutting concerns**
- `backend/config.py` — global config, env vars, DB and MinIO clients
- `backend/background_tasks.py` — document processing pipeline and async status updates
- `backend/llm_integration.py` — how prompts and responses are constructed
- `frontend/src/services/api.ts` — frontend API client; follow its usage when changing endpoints

**Examples to reference**
- Adding a new API route in monolith: modify `backend/app.py`, add Pydantic schema in `backend/schemas.py`, update DB model in `backend/models.py` if persistent, and add CRUD helper in `backend/utils.py`.
- Adding a new microservice: mirror the structure in `microservices/user-service/` and add it to `microservices/docker-compose.yml`, then update API Gateway routes in `microservices/gateway/`.

**Limitations (do not assume otherwise)**
- This repository is intended for local demo and experimentation — some security and scaling aspects are simplified (e.g., JWT secrets, local SQLite, mock LLM).
- Tests and CI are minimal; do not assume a full test harness exists unless you open a specific service's directory and confirm tests there.

# Copilot / AI agent instructions — Local Deployment repo

**Purpose**: Help AI coding assistants become productive immediately in this repository by describing the architecture, common workflows, conventions, and key integration points discovered in the codebase.

**Big Picture**: The project provides two related topologies:
- **Local monolith for demo**: `docker-compose.yml` starts a React frontend (port 3000), a FastAPI backend (port 8000), and MinIO (port 9001). See `README.md` and `architecture.md` for diagrams and data flow.
- **Microservices variant**: `microservices/` contains an independent microservices layout (API gateway + user, document, analysis, analytics, storage services). Each service follows Clean Architecture (`domain/`, `application/`, `infrastructure/`). See `microservices/README.md`.

**Key files / places to read (high priority)**
- **`README.md`**: quick start, env vars, architecture summary, default credentials.
- **`architecture.md`**: component diagram, data flow, and local-vs-cloud differences.
- **`microservices/README.md`**: detailed microservices boundaries, ports, health endpoints and deploy scripts.
- **`backend/`**: monolithic FastAPI implementation — read `backend/app.py`, `backend/config.py`, `backend/llm_integration.py`, and `backend/background_tasks.py` to understand request handling and async processing.
- **`frontend/src/`**: React + TypeScript UI; main components live under `components/` and `pages/`.
- **`docker-compose.yml` & `docker-compose.lmstudio.yml`**: local orchestration and alternate compose configs.

**Architecture notes agents must know**
- The local demo intentionally collapses multiple microservices into a single FastAPI backend (`backend/`) for simplicity; however the repo also contains a true microservices layout under `microservices/` implementing the API Gateway pattern.
- Storage: MinIO is used as S3-compatible storage; uploaded documents and exports persist to `./data` (mounted volumes in compose).
- LLM usage: LLM integration is configurable via env `LLM_MODE` (`mock` or `openai`) and the codepaths live in `backend/llm_integration.py` (monolith) and service-level equivalents in `microservices/*/`.

**Developer workflows (concrete commands)**
- Start local demo (recommended for quick iteration):
  - `docker-compose up -d` (run from repo root)
  - `docker-compose logs -f` to follow logs
- Run microservices variant:
  - `chmod +x microservices/build-and-deploy.sh && ./microservices/build-and-deploy.sh`
- Frontend local dev / build:
  - `cd frontend && npm install` then `npm start` (dev) or `npm run build` (production bundle used by compose)
- Backend local dev (no containers):
  - `cd backend && pip install -r requirements.txt && python app.py`
- Health checks (useful for integration tests):
  - Gateway: `http://localhost:8000/health`
  - Services: `http://localhost:8001/health` .. `:8005/health` (see `microservices/README.md`)

**Conventions & patterns specific to this repo**
- Monolith vs microservices: prefer reading the monolith code under `backend/` to understand runtime behaviour when `docker-compose.yml` is used — the microservices tree follows the same domain/use-case split but scattered by service.
- Clean Architecture in `microservices/`: each service is organized as `domain/`, `application/`, `infrastructure/`. New services should follow this pattern.
- Auth: JWT tokens are used across the stack; `backend/auth.py` and microservice `infrastructure/auth.py` implement token handling and role checks.
- Data ownership: each service owns its DB and storage — avoid changing another service's data layer directly; use service APIs for cross-service interaction.

**Integration points and external dependencies**
- MinIO (S3-compatible) — see `docker-compose.yml` mounts and the `STORAGE_PATH`/MinIO client created in `backend/config.py`.
- OpenAI: enabled when `LLM_MODE=openai` and `OPENAI_API_KEY` set. Mock mode (`LLM_MODE=mock`) simulates LLM responses (useful for offline testing).
- Docker: primary orchestration for demo; microservices can be run individually for development.

**When editing code, pay attention to these files for cross-cutting concerns**
- `backend/config.py` — global config, env vars, DB and MinIO clients
- `backend/background_tasks.py` — document processing pipeline and async status updates
- `backend/llm_integration.py` — how prompts and responses are constructed
- `frontend/src/services/api.ts` — frontend API client; follow its usage when changing endpoints

**Examples to reference**
- Adding a new API route in monolith: modify `backend/app.py`, add Pydantic schema in `backend/schemas.py`, update DB model in `backend/models.py` if persistent, and add CRUD helper in `backend/utils.py`.
- Adding a new microservice: mirror the structure in `microservices/user-service/` and add it to `microservices/docker-compose.yml`, then update API Gateway routes in `microservices/gateway/`.

**Limitations (do not assume otherwise)**
- This repository is intended for local demo and experimentation — some security and scaling aspects are simplified (e.g., JWT secrets, local SQLite, mock LLM).
- Tests and CI are minimal; do not assume a full test harness exists unless you open a specific service's directory and confirm tests there.

**If you are unsure where to change something**
- Find the user-facing behavior in the UI (`frontend/src/pages/*`) then follow the call into `frontend/src/services/api.ts` and the backend endpoint in `backend/app.py`.

Please review this draft and tell me if you want more detail in any of the following areas: service ports/hosts, example PR checklist, or quick-edit recipes (add route, add service, re-run migrations).
````