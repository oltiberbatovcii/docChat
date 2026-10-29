# CLAUDE.md — DocChat (RAG Learning Project)

> This file tells Claude Code how to build this project **and how to work with me**.
> Read it fully before doing anything. Follow the "Working Rules" on every step.

---

## 1. Project Overview

**DocChat** is a "chat with your documents" app. Users upload PDFs and ask questions; the app answers using only the uploaded content and cites the source (file + page).

**Purpose:** this is a **learning project**. I want hands-on practice with every skill below, at a **minimal, playground scale**. Prefer simple, readable code over clever or "enterprise" code. No over-engineering.

### Skills this project must give me practice with
| Skill | Where it's practiced |
|---|---|
| Python for AI | Whole backend |
| LLMs | Answer generation (Phase 5) |
| RAG | Ingestion → retrieval → generation (Phases 2–5) |
| APIs | FastAPI backend consumed by React frontend |
| Vector databases | ChromaDB (Phase 3), optional swap later |
| Prompt engineering | Versioned prompts + experiments (Phases 5, 8) |
| Evaluation metrics | Eval dataset + scripts (Phase 7) |
| Version control | I commit & push manually at every checkpoint |
| Containerization | Docker + Docker Compose to package and run locally (Phase 9) |
| Agile | Each phase = a small sprint with clear done criteria |

### Out of scope (do NOT build unless I ask)
- Authentication / users / multi-tenancy
- Kubernetes, CI/CD, cloud infrastructure (Docker is used **only** to package and run the app locally, see Phase 9)
- Databases other than the vector store
- Complex state management (no Redux etc.)

---

## 2. Working Rules for Claude Code (IMPORTANT)

### 2.1 Go step by step
- Work **one phase at a time**, and inside a phase, **one task at a time**.
- Never start the next phase without my explicit "continue" / "next".
- Keep each change small enough that I can read and understand all of it.

### 2.2 Git — I do it myself
- **Never run `git commit`, `git push`, `git merge`, or create branches yourself.**
- You may run `git status` and `git diff` to show me what changed.
- At every **Git Checkpoint**, stop and give me the exact commands to run, e.g.:
  ```bash
  git checkout -b feat/ingestion
  git add backend/app/services/chunking.py backend/tests/test_chunking.py
  git commit -m "feat(ingestion): add text chunking with overlap"
  git push -u origin feat/ingestion
  ```
- Use **Conventional Commits**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`.
- Use **one branch per phase** (`feat/<phase-name>`). After I push, tell me how to open a PR and merge it into `main` on GitHub, then switch back:
  ```bash
  git checkout main && git pull
  ```

### 2.3 Explain everything in chat (after every task)
After finishing each task, write an explanation in the chat using **exactly this format**:

```
## ✅ What I just built
One or two sentences in plain words.

## 📁 Files changed
- path/to/file.py — what it does (1 line each)

## 🧠 How it works
Step-by-step explanation in simple language. Explain WHY, not just WHAT.
Include a tiny code excerpt if it helps.

## 📚 Concepts you just learned
- Concept name — 1–2 sentence explanation (e.g. "Chunk overlap — ...")

## 🧪 How to try it yourself
Exact commands to run and what output to expect.

## ⏭️ Next step
What the next task is (do not start it until I say so).
```

At the end of each phase, also add the **Git Checkpoint** block with the commands for me to run.

### 2.4 Keep a learning log
- After each task, append a short entry to `docs/LEARNING_LOG.md` (date, phase, what was built, key concepts).
- Update the **Progress Tracker** (section 7 of this file) by ticking off completed tasks.
- Record any important design choice in `docs/DECISIONS.md` (what we chose, alternatives, why).

### 2.5 Code quality rules
- Type hints on all Python functions; Pydantic models for API request/response bodies.
- Small functions, clear names, short docstrings. Comments explain *why*.
- No secrets in code. Config comes from `.env` via `pydantic-settings`; always keep `.env.example` updated.
- Write a simple test for each piece of core logic (chunking, retrieval, API endpoints).
- Run `ruff check`, `ruff format`, and `pytest` before saying a backend task is done.
- Run `npm run lint` and `npm run build` before saying a frontend task is done.
- If something fails, show me the error and explain it before fixing it.
- If you're unsure about a choice, ask me instead of guessing.

---

## 3. Tech Stack (minimal, industry standard)

### Backend
| Purpose | Tool |
|---|---|
| Language | Python 3.11+ |
| Package/env manager | `uv` (fallback: `venv` + `pip`) |
| API framework | FastAPI + Uvicorn |
| Config | `pydantic-settings` + `.env` |
| PDF parsing | `pypdf` |
| Embeddings | `sentence-transformers` (`all-MiniLM-L6-v2`, free, runs locally) |
| Vector database | ChromaDB (persistent local mode) |
| LLM | **Ollama** (free, local, default) — optional: Anthropic or OpenAI API via env setting |
| Testing | `pytest` + FastAPI `TestClient` |
| Lint/format | `ruff` |
| Evaluation | Custom Python eval script (+ optional `ragas` later) |

### Frontend
| Purpose | Tool |
|---|---|
| Framework | React + TypeScript |
| Build tool | Vite |
| HTTP | Native `fetch` wrapped in a small API client |
| Styling | Plain CSS (one global file + CSS modules if needed) |
| Lint | ESLint (comes with the Vite template) |

### Tooling
- Git + GitHub (manual commits by me)
- Docker + Docker Compose (local packaging and testing only)
- GitHub Issues as a lightweight sprint board (optional, one issue per task)

---

## 4. Folder Structure (target)

Build this gradually — only create folders when a phase needs them.

```
docchat/
├── CLAUDE.md                  # This file
├── README.md                  # Project overview, setup, results
├── .gitignore
├── docker-compose.yml         # Runs backend + frontend together (Phase 9)
├── docs/
│   ├── LEARNING_LOG.md        # Running log of what was built & learned
│   └── DECISIONS.md           # Design decisions and why
│
├── backend/
│   ├── Dockerfile             # Backend image (Phase 9)
│   ├── .dockerignore
│   ├── pyproject.toml         # Dependencies + ruff/pytest config
│   ├── .env.example           # Template for environment variables
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app creation, CORS, router registration
│   │   ├── core/
│   │   │   └── config.py      # Settings loaded from .env
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── health.py      # GET /health
│   │   │       ├── documents.py   # POST /documents (upload), GET /documents
│   │   │       ├── search.py      # POST /search (retrieval only)
│   │   │       └── chat.py        # POST /chat (full RAG)
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── pdf_loader.py      # PDF → text per page
│   │   │   ├── chunking.py        # Text → overlapping chunks + metadata
│   │   │   ├── embeddings.py      # Text → vectors
│   │   │   ├── vector_store.py    # ChromaDB add/query wrapper
│   │   │   ├── llm.py             # LLM client (Ollama / API provider)
│   │   │   └── rag.py             # Orchestrates retrieve → prompt → generate
│   │   └── prompts/
│   │       └── answer_prompts.py  # Versioned prompt templates (v1, v2, ...)
│   ├── evals/
│   │   ├── dataset.jsonl      # Hand-written question / expected answer / source
│   │   ├── run_evals.py       # Runs evals and prints metrics
│   │   └── results/           # Saved eval runs (JSON) for comparison
│   ├── tests/
│   │   ├── test_chunking.py
│   │   ├── test_vector_store.py
│   │   └── test_api.py
│   └── data/                  # GITIGNORED: uploaded PDFs + Chroma DB files
│
└── frontend/
    ├── Dockerfile             # Multi-stage: build with Node, serve with Nginx (Phase 9)
    ├── .dockerignore
    ├── nginx.conf             # Serves the built React app
    ├── package.json
    ├── .env.example           # VITE_API_URL=http://localhost:8000
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/
        │   └── client.ts      # All fetch calls to the backend live here
        ├── types.ts           # Shared TypeScript types (mirror backend schemas)
        ├── components/
        │   ├── FileUpload.tsx
        │   ├── ChatWindow.tsx
        │   ├── MessageBubble.tsx
        │   └── SourceList.tsx
        └── styles/
            └── global.css
```

---

## 5. API Contract (target)

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | `/health` | — | `{ "status": "ok" }` |
| POST | `/documents` | multipart PDF file | `{ document_id, filename, pages, chunks }` |
| GET | `/documents` | — | list of uploaded documents |
| POST | `/search` | `{ query, top_k }` | list of chunks with text, filename, page, score |
| POST | `/chat` | `{ question, top_k }` | `{ answer, sources: [{filename, page, snippet}] }` |

FastAPI auto-docs at `http://localhost:8000/docs` — point me to it whenever a new endpoint is added.

---

## 6. Phases (Sprints)

Each phase ends with: explanation in chat → Git Checkpoint → wait for me.

### Phase 0 — Project setup
**Goal:** empty but well-structured repo on GitHub.
- [x] Explain how I should create an empty GitHub repo named `docchat` (no README) and connect it (`git init`, `git remote add origin ...`).
- [x] Create `.gitignore` (Python, Node, `.env`, `backend/data/`, `node_modules/`, `__pycache__/`, `.venv/`).
- [x] Create `README.md` (short placeholder), `docs/LEARNING_LOG.md`, `docs/DECISIONS.md`.
- **Done when:** repo exists on GitHub with these files on `main`.
- **Git Checkpoint:** commit directly to `main`: `chore: initial project setup`.

### Phase 1 — Backend skeleton
**Goal:** a running FastAPI app with config and one tested endpoint.
- [ ] Init backend with `uv`, add FastAPI, Uvicorn, pydantic-settings, pytest, ruff.
- [ ] `app/core/config.py` with settings; `.env.example`.
- [ ] `app/main.py` with CORS (allow the Vite dev URL) and `GET /health`.
- [ ] `tests/test_api.py` testing `/health`.
- **Concepts to explain:** virtual envs, dependency management, ASGI, routers, CORS, env-based config.
- **Done when:** `uvicorn app.main:app --reload` works, `/docs` loads, tests pass.
- **Branch:** `feat/backend-skeleton`

### Phase 2 — Document ingestion (no AI yet)
**Goal:** turn a PDF into clean, overlapping chunks with metadata.
- [ ] `services/pdf_loader.py`: extract text per page.
- [ ] `services/chunking.py`: split by characters with configurable `chunk_size` and `chunk_overlap`; keep `filename`, `page`, `chunk_index` metadata.
- [ ] Unit tests for chunking edge cases (empty text, short text, overlap correctness).
- [ ] Add a sample PDF to try it (or tell me where to put my own).
- **Concepts to explain:** why we chunk, chunk size vs. overlap trade-offs, metadata for citations.
- **Branch:** `feat/ingestion`

### Phase 3 — Embeddings + vector database
**Goal:** store chunks as vectors and expose upload.
- [ ] `services/embeddings.py`: load the sentence-transformers model once, embed a list of texts.
- [ ] `services/vector_store.py`: ChromaDB persistent client; `add_chunks()` and `query()`.
- [ ] `POST /documents` and `GET /documents` endpoints.
- [ ] Tests (use a temporary Chroma directory).
- **Concepts to explain:** what an embedding is, cosine similarity, what a vector DB adds over a list, collections, persistence.
- **Branch:** `feat/vector-store`

### Phase 4 — Retrieval (the "R" in RAG)
**Goal:** semantic search over uploaded docs, without any LLM.
- [ ] `POST /search` returning top-k chunks with scores.
- [ ] Let me try queries in `/docs` and show me how scores change with wording.
- **Concepts to explain:** top-k, similarity scores, why retrieval quality decides answer quality.
- **Branch:** `feat/retrieval`

### Phase 5 — LLM generation + prompt engineering v1
**Goal:** full RAG answers with citations.
- [ ] Help me install Ollama and pull a small model (verify with `ollama list`).
- [ ] `services/llm.py`: small client with a `generate(prompt) -> str` function; provider chosen via `.env` (`ollama` default; `anthropic`/`openai` optional).
- [ ] `prompts/answer_prompts.py`: `PROMPT_V1` — answer only from context, cite `[filename p.X]`, say "I don't know" if not in context.
- [ ] `services/rag.py`: retrieve → build prompt → generate → return answer + sources.
- [ ] `POST /chat` endpoint + test (mock the LLM in tests).
- **Concepts to explain:** context window, system vs. user prompt, grounding, hallucination, why we mock LLMs in tests.
- **Branch:** `feat/rag-chat`

### Phase 6 — React frontend
**Goal:** a simple UI that uses the API.
- [ ] Scaffold with `npm create vite@latest frontend -- --template react-ts`.
- [ ] `api/client.ts` with typed functions: `uploadDocument`, `listDocuments`, `sendChat`.
- [ ] Components: `FileUpload`, `ChatWindow`, `MessageBubble`, `SourceList`.
- [ ] Loading and error states (simple, no libraries).
- [ ] `VITE_API_URL` in `.env.example`.
- **Concepts to explain:** components, props, state (`useState`), effects, async fetch, how the frontend talks to the API, CORS in practice.
- **Done when:** I can upload a PDF and chat with it in the browser.
- **Branch:** `feat/frontend`

### Phase 7 — Evaluation
**Goal:** measure quality with numbers.
- [ ] Help me write `evals/dataset.jsonl` with ~15–20 items: `question`, `expected_answer`, `expected_source` (filename + page). Include 3 questions that are NOT answerable from the docs.
- [ ] `evals/run_evals.py` computing:
  - **Retrieval hit rate@k** — is the expected page in the top-k?
  - **MRR** — how high the correct chunk ranks
  - **Answer correctness** — LLM-as-judge score (1–5) vs. expected answer
  - **Refusal accuracy** — says "I don't know" on unanswerable questions
- [ ] Save each run to `evals/results/<timestamp>_<label>.json` and print a summary table.
- **Concepts to explain:** why evals matter, retrieval vs. generation metrics, LLM-as-judge pros/cons.
- **Branch:** `feat/evals`

### Phase 8 — Experiments (prompt engineering + RAG tuning)
**Goal:** improve the numbers and document it.
- [ ] Add `PROMPT_V2` (e.g. few-shot example, stricter citation format) selectable via config.
- [ ] Run evals comparing: prompt v1 vs v2, chunk size (e.g. 300 vs 800), top_k (3 vs 6).
- [ ] Produce a comparison table and record conclusions in `docs/DECISIONS.md`.
- **Concepts to explain:** controlled experiments (change one thing at a time), trade-offs found.
- **Branch:** `feat/experiments`

### Phase 9 — Docker (package & run locally)
**Goal:** run the whole app with one command: `docker compose up --build`.
Keep it minimal and local-only. Explain every line of each Dockerfile and the compose file.
- [ ] Check Docker is installed (`docker --version`, `docker compose version`); if not, tell me how to install Docker Desktop.
- [ ] `backend/Dockerfile`:
  - Slim Python base image, install `uv`, copy `pyproject.toml` + lock file **first** (layer caching), then the app code.
  - Install **CPU-only PyTorch** to keep the image small (sentence-transformers pulls torch).
  - Run Uvicorn on `0.0.0.0:8000`.
- [ ] `frontend/Dockerfile`: multi-stage build — stage 1 `node` runs `npm ci && npm run build`; stage 2 `nginx:alpine` serves `dist/` using `nginx.conf`.
  - `VITE_API_URL` is passed as a build arg (`http://localhost:8000`, because the browser calls the API from the host).
- [ ] `.dockerignore` for both (exclude `node_modules`, `.venv`, `data/`, `.env`, `__pycache__`, `.git`).
- [ ] `docker-compose.yml` at the root:
  - `backend` service: port `8000:8000`, `env_file: backend/.env`, named volumes for `data/` (Chroma + uploads) and the Hugging Face model cache so nothing re-downloads on restart.
  - `frontend` service: port `5173:80`, `depends_on: backend`.
  - **Ollama stays on my host machine** (not in a container). Backend reaches it at `http://host.docker.internal:11434`; add `extra_hosts: ["host.docker.internal:host-gateway"]` so this also works on Linux. Make the Ollama URL a setting in `config.py`.
  - A `healthcheck` on the backend hitting `/health`.
- [ ] Walk me through testing it: build, open `http://localhost:5173`, upload a PDF, chat, then `docker compose down` and `up` again to prove the data persisted in the volume.
- [ ] Teach me the basic debugging commands: `docker compose ps`, `docker compose logs -f backend`, `docker compose exec backend sh`, `docker compose down -v` (and warn that `-v` deletes the volumes).
- **Concepts to explain:** image vs. container, layers & caching, multi-stage builds, ports, volumes, environment variables in containers, container networking (`localhost` inside a container ≠ my machine), healthchecks.
- **Done when:** a fresh `docker compose up --build` gives me a working app in the browser and data survives a restart.
- **Branch:** `feat/docker`

### Phase 10 — Wrap-up
**Goal:** a portfolio-ready repo.
- [ ] Final `README.md`: what it is, architecture diagram (Mermaid), setup steps (both local dev **and** Docker), how to run evals, **results table before/after**, what I learned.
- [ ] Review the code with me and point out anything worth refactoring.
- **Branch:** `docs/readme`

### Stretch goals (only if I ask)
- Streaming responses (Server-Sent Events) to the frontend
- Swap ChromaDB for Qdrant or pgvector behind the same `vector_store.py` interface
- Hybrid search (keyword BM25 + vector) or a re-ranker
- Try `ragas` for additional metrics
- Small LoRA fine-tune of an open model vs. prompting (separate notebook)
- Run Ollama as a container in `docker-compose.yml` too
- Simple free deployment (Hugging Face Spaces / Render + Vercel)

---

## 7. Progress Tracker

Claude Code: update this after each task.

| Phase | Status |
|---|---|
| 0 — Setup | 🟨 In progress (files ready, waiting for first push) |
| 1 — Backend skeleton | ⬜ Not started |
| 2 — Ingestion | ⬜ Not started |
| 3 — Embeddings + vector DB | ⬜ Not started |
| 4 — Retrieval | ⬜ Not started |
| 5 — LLM + prompts | ⬜ Not started |
| 6 — React frontend | ⬜ Not started |
| 7 — Evaluation | ⬜ Not started |
| 8 — Experiments | ⬜ Not started |
| 9 — Docker | ⬜ Not started |
| 10 — Wrap-up | ⬜ Not started |

Status legend: ⬜ Not started · 🟨 In progress · ✅ Done

---

## 8. Useful Commands (keep updated as the project grows)

```bash
# Backend
cd backend
uv sync                                  # install dependencies
uv run uvicorn app.main:app --reload     # run API at http://localhost:8000
uv run pytest                            # run tests
uv run ruff check . && uv run ruff format .
uv run python evals/run_evals.py --label baseline

# Frontend
cd frontend
npm install
npm run dev                              # http://localhost:5173
npm run lint && npm run build

# Docker (from the project root, Phase 9+)
docker compose up --build                # build images and start everything
docker compose ps                        # see running containers
docker compose logs -f backend           # follow backend logs
docker compose exec backend sh           # open a shell inside the backend container
docker compose down                      # stop (keeps data volumes)
docker compose down -v                   # stop AND delete volumes (wipes uploaded data)
```

---

## 9. How to Start

When I say **"start"**, begin with **Phase 0**: explain what we're about to do, then walk me through creating the GitHub repo, then create the setup files, then explain and give me the Git Checkpoint commands.
