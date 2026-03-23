# Clio - Red Team Activity Logger

A comprehensive platform for logging, tracking, and analyzing red team activities with advanced relationship mapping and audit capabilities.

> **PoC Notice**: This setup prioritises convenience over security. SSL/TLS, Redis
> encryption, HSTS, and secure cookie flags have all been intentionally disabled.
> **Do not expose this to untrusted networks or use it in production as-is.**
> See the _Production Hardening_ section at the bottom for what needs to be
> re-enabled before going to production.

## Features

- **Activity Logging**: Track and document red team activities with detailed metadata
- **User Management**: Secure authentication with JWT tokens and role-based access control
- **Audit Trail**: Complete audit logging for compliance and security analysis
- **API Keys**: Secure API access management for automation and integrations
- **Relationship Mapping**: Advanced service for mapping and analyzing entity relationships
- **Real-time Updates**: Redis-powered caching and real-time data synchronization

## Architecture

- **Frontend**: React-based web interface with Vite build system
- **Backend**: Django REST API with PostgreSQL database
- **Relation Service**: Specialized microservice for relationship analysis
- **Infrastructure**: Docker Compose orchestration with nginx reverse proxy

## Quick Start

### Prerequisites

- Docker and Docker Compose (v2.0+)
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd literate-train/clio
```

### 2. Generate Environment Files

Run the generator to create `.env` files with random secrets for all services:

```bash
python -m generate_env
```

This creates `clio/.env`, `clio/backend/.env`, and `clio/relation_service/.env`.
Alternatively, copy the example and edit manually:

```bash
cp .env.example .env
# Edit .env and fill in POSTGRES_PASSWORD, REDIS_PASSWORD, JWT_SECRET, etc.
```

### 3. Build and Start Services

```bash
# Build and start all services
docker compose up --build -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 4. Database Setup

```bash
# Run database migrations
docker compose exec backend python manage.py migrate

# Create a superuser account
docker compose exec backend python manage.py createsuperuser

# Seed initial data (optional)
docker compose exec backend python manage.py seed_initial_passwords
```

### 5. Access the Application

- **Web Interface**: http://localhost
- **API Documentation**: http://localhost/api/schema/swagger-ui/
- **Admin Panel**: http://localhost/api/admin/

## Development Setup

For development with hot-reloading and debugging:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

The dev override maps ports `8080` (HTTP) for nginx, `8001` for the backend, `8002`
for the relation service, `5432` for PostgreSQL, and `6379` for Redis.

### Install Local Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies
cd ../frontend
npm install
```

## API Usage

### Authentication

```bash
# Login to get JWT token
curl -X POST http://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token in subsequent requests
curl -X GET http://localhost/api/activities/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### API Keys

```bash
# Create API key
curl -X POST http://localhost/api/api-keys/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "permissions": ["read", "write"]}'

# Use API key
curl -X GET http://localhost/api/activities/ \
  -H "X-API-Key: YOUR_API_KEY"
```

## Maintenance

### Backup Database

```bash
# Create backup
docker compose exec db pg_dump -U clio redteamlogger > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose exec -T db psql -U clio redteamlogger < backup_file.sql
```

### Update Services

```bash
# Pull latest images and rebuild
docker compose pull
docker compose up --build -d

# Run any pending migrations
docker compose exec backend python manage.py migrate
```

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend

# With timestamps
docker compose logs -f -t
```

### Service Management

```bash
# Stop services
docker compose stop

# Restart specific service
docker compose restart backend

# Remove everything (including volumes)
docker compose down -v
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure port 80 is available (8080 in dev mode)
2. **Database connection**: Verify PostgreSQL is healthy with `docker compose ps`
3. **Redis connection**: Verify Redis is healthy with `docker compose ps`

### Health Checks

```bash
# Check all service health
docker compose ps

# Test database connection
docker compose exec backend python manage.py dbshell

# Test Redis connection
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" ping
```

### Logs and Debugging

```bash
# Backend Django logs
docker compose logs backend

# Database logs
docker compose logs db

# nginx access logs
docker compose logs nginx-proxy
```

## Production Hardening

Before using this in any non-local environment, re-enable the security features
that were stripped out for PoC convenience:

1. **TLS on nginx** – restore the HTTPS server block and HTTP→HTTPS redirect in
   `nginx/nginx.conf`, mount TLS certs into the container.
2. **Redis TLS + encryption** – restore `ssl=True`, `ssl_cert_reqs`, and the
   `EncryptedRedis` AES-256-GCM wrapper in `backend/common/redis_client.py`.
   Add `REDIS_SSL=true` and `REDIS_ENCRYPTION_KEY` back to env files.
3. **PostgreSQL SSL** – re-add `ssl=on` and cert paths to the `db` command in
   `compose.yaml`, mount `./certs/postgres`.
4. **Django security settings** – restore `SECURE_SSL_REDIRECT`, HSTS headers,
   `SESSION_COOKIE_SECURE`, and `CSRF_COOKIE_SECURE` in
   `backend/backend/settings/production.py`.
5. **Certificate generation** – run `python -m generate_env` after restoring the
   `generate_certs()` call in `generate_env/__main__.py`, or use Let's Encrypt.
6. **Secrets management** – use a proper secrets manager; do not commit `.env` files.
7. **Log aggregation and monitoring**
8. **Automated backups**
9. **Container orchestration** (Kubernetes, Docker Swarm) for production scale

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Your License Here]
