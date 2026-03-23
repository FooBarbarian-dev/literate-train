# Clio - Red Team Activity Logger

A comprehensive platform for logging, tracking, and analyzing red team activities with advanced relationship mapping and audit capabilities.

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
- **Security**: TLS encryption, secure authentication, and network isolation

## Quick Start

### Prerequisites

- Docker and Docker Compose (v2.0+)
- Git

### 1. Clone the Repository

```bash
git clone <repository-url>
cd literate-train/clio
```

### 2. Generate Environment Files and SSL Certificates

Run the bundled generator from inside the `clio/` directory. It creates all `.env`
files with cryptographically-random secrets **and** generates self-signed TLS
certificates for every service in one step:

```bash
cd clio
pip install cryptography   # only needed the first time
python -m generate_env
```

The generator writes:
- `clio/.env` – root compose environment (passwords, secrets)
- `clio/backend/.env` – backend service environment
- `clio/relation_service/.env` – relation-service environment
- `clio/certs/` – CA, server, Redis, and PostgreSQL TLS certificates

> **Let's Encrypt (production):** Pass `--letsencrypt` to configure certificate
> paths for a Let's Encrypt setup instead of self-signed certs.

### 4. Build and Start Services

```bash
# Build and start all services
docker compose up --build -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### 5. Database Setup

```bash
# Run database migrations
docker compose exec backend python manage.py migrate

# Create a superuser account
docker compose exec backend python manage.py createsuperuser

# Seed initial data (optional)
docker compose exec backend python manage.py seed_initial_passwords
```

### 6. Access the Application

- **Web Interface**: https://localhost (or your configured domain)
- **API Documentation**: https://localhost/api/schema/swagger-ui/
- **Admin Panel**: https://localhost/api/admin/

## Development Setup

For development with hot-reloading and debugging:

### 1. Start with the Development Override

A ready-made `compose.dev.yaml` override is included. It enables hot-reloading,
exposes database and Redis ports, and disables TLS on the local database so you
don't need client certificates during development:

```bash
docker compose -f compose.yaml -f compose.dev.yaml up --build
```

The dev override maps:
- nginx → `http://localhost:8080` / `https://localhost:8443`
- backend → `http://localhost:8001` (direct access)
- relation-service → `http://localhost:8002` (direct access)
- PostgreSQL → `localhost:5432`
- Redis → `localhost:6379`

### 2. Install Local Dependencies (optional, for IDE tooling)

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
curl -X POST https://localhost/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use token in subsequent requests
curl -X GET https://localhost/api/activities/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### API Keys

```bash
# Create API key
curl -X POST https://localhost/api/api-keys/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "permissions": ["read", "write"]}'

# Use API key
curl -X GET https://localhost/api/activities/ \
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

1. **Port conflicts**: Ensure ports 80, 443 are available
2. **Permission issues**: Check file permissions on certificate files
3. **Database connection**: Verify PostgreSQL is healthy with `docker compose ps`
4. **SSL errors**: Ensure certificates are properly generated and mounted

### Health Checks

```bash
# Check all service health
docker compose ps

# Test database connection
docker compose exec backend python manage.py dbshell

# Test Redis connection
docker compose exec redis redis-cli --tls --cert /tls/redis.crt --key /tls/redis.key --cacert /tls/ca.crt ping
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

## Production Deployment

For production deployment, consider:

1. Use proper SSL certificates from a CA (Let's Encrypt, etc.)
2. Configure proper domain names and DNS
3. Set up log aggregation and monitoring
4. Configure automated backups
5. Use secrets management for sensitive data
6. Set up container orchestration (Kubernetes, Docker Swarm)
7. Implement proper CI/CD pipelines

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Your License Here]