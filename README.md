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
- Python 3.9+ (only for `generate_env`; Docker handles everything else)

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
curl -X POST http://localhost:3000/api/auth/login/ \
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
