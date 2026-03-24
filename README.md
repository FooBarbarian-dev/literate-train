# Clio - Red Team Activity Logger

A platform for logging, tracking, and analysing red team activities with relationship mapping and audit capabilities.

> **PoC Notice**: This setup prioritises convenience over security. SSL/TLS,
> Redis encryption, HSTS, and secure cookie flags are all disabled. The Vite
> dev server is used instead of a production build+nginx stack. Passwords are
> stored in plaintext `.env` files and the default admin/user credentials are
> auto-generated. **Do not expose this to untrusted networks.** See
> _Production Hardening_ at the bottom for what to re-enable before going live.

## Architecture

| Service | What it does | Port |
|---|---|---|
| `frontend` | React app (Vite dev server + proxy) | 3000 |
| `backend` | Django REST API | internal |
| `relation-service` | Relationship microservice | internal |
| `redis` | Cache / Celery broker | internal |
| `db` | PostgreSQL | internal |

The Vite dev server proxies `/api` → `backend:3001` and `/relation-service` →
`relation-service:3002`, so no separate reverse proxy is needed.

## Quick Start

### Prerequisites

- Docker and Docker Compose v2+
- Python 3.12+ (for local development; Docker handles everything else)
- [Conda](https://docs.conda.io/) or [Mamba](https://mamba.readthedocs.io/) (recommended for local dev)

### 1. Clone

```bash
git clone <repository-url>
cd literate-train/clio
```

### 2. Generate env files

Using the installed CLI (see [Local Development](#local-development) below):

```bash
clio-env
```

Or without installing the package:

```bash
python -m generate_env
```

This writes `clio/.env`, `clio/backend/.env`, and `clio/relation_service/.env`
with random passwords and secrets. That's all the setup needed — no
certificates, no manual secret editing.

> **Security shortcut**: The generated passwords are printed to the terminal
> and stored in plaintext `.env` files. The admin and user passwords are in
> `backend/.env` as `ADMIN_PASSWORD` and `USER_PASSWORD`. In production you
> would use a secrets vault instead.

### 3. Start

```bash
docker compose up --build -d
```

The backend and relation-service containers automatically:
- Wait for the database to be ready
- Run Django migrations
- Collect static files (for Django admin CSS)
- Seed initial admin/user passwords into Redis

No manual `migrate` or `seed` step required.

### 4. (Optional) Populate demo data

```bash
docker compose exec backend python manage.py seed_demo_data
```

This creates three realistic red-team operations (NIGHTFALL, IRON GATE,
SILENT STORM) with associated log entries and tags — useful for exploring
the UI immediately.

To reset and re-seed:

```bash
docker compose exec backend python manage.py seed_demo_data --clear
```

### 5. Login

- **App**: http://localhost:3000
- **API docs**: http://localhost:3000/api/schema/swagger-ui/
- **Admin panel**: http://localhost:3000/api/admin/

Log in with any username using the password from `backend/.env`:
- Use `ADMIN_PASSWORD` value with any username for **admin** access
- Use `USER_PASSWORD` value with any username for **regular user** access

> **Security shortcut**: There is no user registration. Any username works
> with the preset passwords. The first login with a preset password will
> prompt for a password change. This is intentionally simple for PoC use.

## App Pages

| Page | Path | Description |
|---|---|---|
| Logs | `/logs` | View and create red team activity log entries |
| Operations | `/operations` | Create and manage operational groupings |
| Tags | `/tags` | Manage tags for categorising log entries |
| Settings | `/settings` | Change password, manage API keys, view sessions |

## API Usage

```bash
# Login (use the ADMIN_PASSWORD from backend/.env)
curl -X POST http://localhost:3000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "YOUR_ADMIN_PASSWORD"}'

# Authenticated request (use the JWT from the login response)
curl http://localhost:3000/api/logs/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# API key request
curl http://localhost:3000/api/logs/ \
  -H "X-API-Key: YOUR_API_KEY"
```

## Maintenance

```bash
# View logs
docker compose logs -f

# Restart a service
docker compose restart backend

# Database backup
docker compose exec db pg_dump -U clio redteamlogger > backup_$(date +%Y%m%d_%H%M%S).sql

# Stop everything (keep volumes)
docker compose down

# Wipe everything including data
docker compose down -v
```

## Troubleshooting

| Symptom | Check |
|---|---|
| Port 3000 already in use | `docker compose ps` or change the port mapping in compose.yaml |
| Backend unhealthy | `docker compose logs backend` — the entrypoint waits for the DB, so check the `db` logs too |
| Redis auth error | Make sure `backend/.env` has `REDIS_URL=redis://:PASSWORD@redis:6379/0` matching the password in `.env` — re-run `python -m generate_env` to regenerate |
| Database not ready | `docker compose logs db` — the entrypoint retries automatically |
| Static files / CSS broken | `docker compose exec backend python manage.py collectstatic --noinput` |
| Demo data missing | `docker compose exec backend python manage.py seed_demo_data` |

## CVE & ATT&CK Chat (RAG Assistant)

The platform includes a cybersecurity chat assistant powered by a local vLLM
instance.  It combines two retrieval sources:

- **Vector store** — MITRE ATT&CK techniques and NVD CVE records, embedded and
  stored locally in Chroma.
- **Live Django DB** — runtime queries against the application's own data (logs,
  operations, tags, etc.) so the assistant can reference current activity.

No OpenAI account or internet-facing AI service is required.

---

### Step 1 — Point at your vLLM instance

Add the following variables to `clio/backend/.env` (create the file if it does
not exist; it is read automatically by Django):

```dotenv
# URL of your vLLM OpenAI-compatible server
VLLM_BASE_URL=http://localhost:8000/v1

# The model name exactly as vLLM reports it (check `GET /v1/models`)
VLLM_MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct

# Leave as-is unless your vLLM instance requires a real key
VLLM_API_KEY=not-needed
```

To find the right `VLLM_MODEL_NAME`:

```bash
curl -s http://localhost:8000/v1/models | python -m json.tool
# Look for the "id" field under "data"
```

---

### Step 2 — Choose an embedding backend

The assistant embeds threat data for semantic search.  Two backends are
supported:

| Setting value | What it does | When to use |
|---|---|---|
| `auto` (default) | Probes vLLM for an embedding model; falls back to local sentence-transformers | Best for most setups |
| `vllm` | Uses vLLM's `/v1/embeddings` endpoint; fails if no embed model is loaded | You serve a dedicated embed model alongside the chat model |
| `sentence-transformers` | Downloads and runs `BAAI/bge-small-en-v1.5` locally (~130 MB) | No embed model on vLLM, or you want reproducible offline embeddings |

```dotenv
# In backend/.env — one of: auto | vllm | sentence-transformers
THREAT_RAG_EMBEDDING_BACKEND=auto
```

If you serve a separate embedding model on vLLM (e.g. `BAAI/bge-small-en-v1.5`
via `--model`), set `THREAT_RAG_EMBEDDING_BACKEND=vllm` and vLLM will be used
for both chat and embeddings.

---

### Step 3 — (Optional) NVD API key

Without an API key the NVD downloader sleeps 6 seconds between pages (NVD's
unauthenticated rate limit).  A free key raises the limit to ~50 req/30 s,
making a full download roughly 10× faster.

Register at: https://nvd.nist.gov/developers/request-an-api-key

```dotenv
NVD_API_KEY=your-nvd-api-key-here
```

---

### Step 4 — Install dependencies

```bash
cd clio
pip install -e ".[rag]"
```

This installs the core platform plus the RAG extras (`django-ai-assistant`,
`langchain-openai`, `langchain-community`, `chromadb`, `sentence-transformers`).

---

### Step 5 — Run the ingestion command

```bash
cd clio/backend
python manage.py ingest_threat_data
```

This will:

1. Download the three MITRE ATT&CK bundles (enterprise, mobile, ICS) and cache
   them under `threat_data/mitre/`.  Re-runs use `If-Modified-Since` headers to
   skip unchanged files.
2. Paginate through the NVD CVE API and cache pages under `threat_data/nvd/`.
   Subsequent runs only fetch records modified since the last sync.
3. Normalise everything into `threat_data/mitre_techniques.jsonl` and
   `threat_data/nvd_cves.jsonl`.
4. Embed and upsert all records into the Chroma vector store at
   `threat_data/chroma_db/`.

**Flags:**

```bash
# Download only — writes JSONL files but does not build the index.
# Use this to collect data on a machine that has internet access,
# then copy the output directory to the air-gapped / production host.
python manage.py ingest_threat_data --download-only

# Index only — reads JSONL files and builds the Chroma vector store.
# No network access required; combine with --data-dir (see below).
python manage.py ingest_threat_data --index-only

# Point at a custom directory for JSONL input (index) or output (download).
# This lets you download on one machine, copy the folder, and index elsewhere.
python manage.py ingest_threat_data --index-only --data-dir /path/to/threat_data
python manage.py ingest_threat_data --download-only --data-dir /mnt/usb/threat_data
```

`--download-only` and `--index-only` are mutually exclusive. Omitting both runs
the full pipeline (download → write JSONL → build index), which is the default.

Expected summary output:

```
Written: 919 techniques, 248000 CVEs.
Upserted 1843 MITRE chunks into 'mitre_techniques' collection.
Upserted 312000 CVE chunks into 'nvd_cves' collection.
Vector store built successfully.
```

---

### Step 6 — Start the server and use the chat

```bash
python manage.py runserver
```

| Interface | URL | Description |
|---|---|---|
| Chat UI | http://localhost:8000/chat/ | Standalone HTML chat page (no login required) |
| Chat API | `POST /api/chat/` | JSON endpoint for programmatic access |

**Chat UI**: open in a browser, type a question, press Enter or Send.

**Chat API:**

```bash
# Start a new conversation
curl -s -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What ATT&CK technique covers LSASS credential dumping?", "thread_id": null}' \
  | python -m json.tool

# Continue the same conversation (pass the returned thread_id)
curl -s -X POST http://localhost:8000/api/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Which CVEs are commonly exploited with that technique?", "thread_id": "UUID-FROM-PREVIOUS-RESPONSE"}' \
  | python -m json.tool
```

**Example response:**

```json
{
  "reply": "LSASS credential dumping maps to ATT&CK technique T1003.001 (OS Credential Dumping: LSASS Memory). CVE-2021-36934 (HiveNightmare/SeriousSAM, CVSS 7.8) allows low-privileged users to read the SAM database...",
  "thread_id": "3f8a2b1c-d4e5-..."
}
```

---

### Querying application data

The assistant can also search the live database when your question references
operation or log data.  It uses a `query_django_db` tool internally.  Example:

```
"Show me logs containing powershell from the last operation"
```

Available models for DB search: `Log`, `Tag`, `Operation`, `EvidenceFile`,
`LogTemplate`, `Relation`, `FileStatus`, `LogRelationship`, `TagRelationship`.

Sensitive fields (`*password*`, `*token*`, `*secret*`, `*key*`, `*hash*`) are
stripped from all results unconditionally.

---

### Troubleshooting

| Symptom | Fix |
|---|---|
| `No vLLM model name configured` (HTTP 503) | Set `VLLM_MODEL_NAME` in `backend/.env` to the model id reported by `GET /v1/models` |
| `RAG retriever unavailable` in logs | Run `python manage.py ingest_threat_data` to build the Chroma index |
| `No embedding model detected at ...` | Set `THREAT_RAG_EMBEDDING_BACKEND=sentence-transformers` in `backend/.env` |
| NVD download is very slow | Add `NVD_API_KEY` to `backend/.env` to lift the rate limit |
| MITRE files not updating | Delete `threat_data/mitre/*.json` to force a fresh download |
| Vector store out of date | Re-run `python manage.py ingest_threat_data` (upsert is idempotent) |

---

## Local Development

### Conda environment (recommended)

```bash
cd clio
conda env create -f environment.yml
conda activate clio
```

This creates a `clio` conda environment with Python 3.13, installs the package
in editable mode with all dev extras (`.[dev]`), and adds standalone tools
(bump-my-version, coverage, pylint).

### Manual setup (pip only)

```bash
cd clio
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Installed CLI commands

Once the package is installed (either via conda or pip), the following commands
are available:

| Command | Description |
|---|---|
| `clio-env` | Generate `.env` files with random secrets for all services |
| `clio-manage` | Django management commands (equivalent to `python manage.py`) |

Examples:

```bash
clio-env                              # Generate env files
clio-manage migrate                   # Run database migrations
clio-manage seed_demo_data            # Populate demo data
clio-manage ingest_threat_data        # Download and index threat intel
clio-manage runserver                 # Start the dev server
```

### Optional dependency groups

Dependencies are split into optional extras in `pyproject.toml`:

| Extra | What it includes | Install with |
|---|---|---|
| `rag` | LangChain, ChromaDB, sentence-transformers | `pip install -e ".[rag]"` |
| `test` | pytest, pytest-django, coverage | `pip install -e ".[test]"` |
| `lint` | pylint, pylint-django, ruff | `pip install -e ".[lint]"` |
| `dev` | All of the above + bump-my-version, debug-toolbar, ipython | `pip install -e ".[dev]"` |

### Running tests

```bash
cd clio
pytest                                # run test suite
coverage run -m pytest && coverage report   # with coverage
```

### Linting

```bash
ruff check backend/ generate_env/     # fast linting
ruff format backend/ generate_env/    # auto-format
pylint backend/                       # deeper analysis
```

---

## Production Hardening

> **This section is critical.** The PoC takes numerous shortcuts that are
> unacceptable for any networked or production deployment.

Before using this outside a local machine, re-enable everything that was
stripped out:

1. **nginx + TLS** — add an nginx service, restore the HTTPS server block with
   TLS certs (Let's Encrypt or self-signed), and redirect HTTP → HTTPS.
2. **Redis TLS + at-rest encryption** — restore `ssl=True` and the
   `EncryptedRedis` AES-256-GCM wrapper in `backend/common/redis_client.py`;
   add `REDIS_SSL=true` and `REDIS_ENCRYPTION_KEY` to env files.
3. **PostgreSQL SSL** — re-add `ssl=on` and cert mounts to the `db` service.
4. **Django security settings** — restore `SECURE_SSL_REDIRECT`, HSTS,
   `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and switch
   `DJANGO_SETTINGS_MODULE` to `backend.settings.production` with a locked-down
   `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`.
5. **Production frontend build** — replace the Vite dev server with
   `npm run build` + `serve` (or nginx) in the frontend Dockerfile.
6. **Secrets management** — use a vault or CI secrets; never commit `.env` files.
7. **User registration / identity** — replace the preset-password scheme with
   proper user accounts, SSO/SAML, or an identity provider.
8. **File storage** — switch from local filesystem to S3 or equivalent with
   proper IAM credentials (see `STORAGES` in settings).
