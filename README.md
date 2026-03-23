# Clio - Red Team Activity Logger

A platform for logging, tracking, and analysing red team activities with relationship mapping and audit capabilities.

> **PoC Notice**: This setup prioritises convenience over security. SSL/TLS,
> Redis encryption, HSTS, and secure cookie flags are all disabled. The Vite
> dev server is used instead of a production build+nginx stack. **Do not
> expose this to untrusted networks.** See _Production Hardening_ at the
> bottom for what to re-enable before going live.

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
- Python 3.9+ (only for `generate_env`; Docker otherwise)

### 1. Clone

```bash
git clone <repository-url>
cd literate-train/clio
```

### 2. Generate env files

```bash
python -m generate_env
```

This writes `clio/.env`, `clio/backend/.env`, and `clio/relation_service/.env`
with random passwords. That's all the setup needed — no certificates, no manual
secret editing.

> If you don't have Python handy, copy the example instead:
> ```bash
> cp .env.example .env
> # then manually create backend/.env and relation_service/.env
> # (see those files' comments for required keys)
> ```

### 3. Start

```bash
docker compose up --build -d
```

### 4. Migrate and seed

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser   # optional
docker compose exec backend python manage.py seed_initial_passwords
```

### 5. Open

- **App**: http://localhost:3000
- **API docs**: http://localhost:3000/api/schema/swagger-ui/
- **Admin**: http://localhost:3000/api/admin/

## API Usage

```bash
# Login
curl -X POST http://localhost:3000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# Authenticated request
curl http://localhost:3000/api/activities/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# API key request
curl http://localhost:3000/api/activities/ \
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
| Backend unhealthy | `docker compose logs backend` |
| Redis auth error | Make sure `backend/.env` has `REDIS_URL=redis://:PASSWORD@redis:6379/0` matching the password in `.env` — re-run `python -m generate_env` to regenerate |
| Database not ready | `docker compose logs db`; migrations may need to run |

## Production Hardening

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
