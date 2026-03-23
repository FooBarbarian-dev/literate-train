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

### 2. Environment Setup

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit the `.env` file with your specific configuration:

```bash
# Database Configuration
POSTGRES_DB=redteamlogger
POSTGRES_USER=clio
POSTGRES_PASSWORD=your_secure_password_here

# Redis Configuration  
REDIS_PASSWORD=your_redis_password_here

# Django Configuration
SECRET_KEY=your_django_secret_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Environment
NODE_ENV=production
```

### 3. Generate SSL Certificates

The application uses TLS encryption. Generate self-signed certificates for development:

```bash
# Create certificate directories
mkdir -p certs/{postgres,redis,nginx}

# Generate CA certificate
openssl genrsa -out certs/ca.key 4096
openssl req -new -x509 -key certs/ca.key -sha256 -subj "/C=US/ST=CA/O=Clio/CN=Clio CA" -days 3650 -out certs/ca.crt

# Generate server certificates for each service
# PostgreSQL
openssl genrsa -out certs/postgres/server.key 4096
openssl req -new -key certs/postgres/server.key -out certs/postgres/server.csr -subj "/C=US/ST=CA/O=Clio/CN=db"
openssl x509 -req -in certs/postgres/server.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -out certs/postgres/server.crt -days 365 -sha256

# Redis
openssl genrsa -out certs/redis/redis.key 4096
openssl req -new -key certs/redis/redis.key -out certs/redis/redis.csr -subj "/C=US/ST=CA/O=Clio/CN=redis"
openssl x509 -req -in certs/redis/redis.csr -CA certs/ca.crt -CAkey certs/ca.key -CAcreateserial -out certs/redis/redis.crt -days 365 -sha256
cp certs/ca.crt certs/redis/ca.crt

# Set proper permissions
chmod 600 certs/postgres/server.key certs/redis/redis.key
chmod 644 certs/postgres/server.crt certs/redis/redis.crt certs/redis/ca.crt
```

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

### 1. Override for Development

Create a `compose.override.yaml` file:

```yaml
services:
  frontend:
    environment:
      - NODE_ENV=development
    volumes:
      - ./frontend:/app
    command: npm run dev

  backend:
    environment:
      - DEBUG=True
    volumes:
      - ./backend:/app
    command: python manage.py runserver 0.0.0.0:3001

  db:
    ports:
      - "5432:5432"  # Expose for local development tools

  redis:
    ports:
      - "6379:6379"  # Expose for local development tools
```

### 2. Install Local Dependencies

```bash
# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies  
cd ../frontend
npm install
```

### 3. Start Development Environment

```bash
docker compose -f compose.yaml -f compose.override.yaml up --build
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