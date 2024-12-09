# Jarvis Assistant Setup Guide

## Prerequisites

### System Requirements
- Python 3.9+
- Docker 20.10+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+

### Development Tools
- Poetry for Python dependency management
- pnpm for Node.js dependency management
- Docker Compose for service orchestration
- Visual Studio Code (recommended)

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/your-org/jarvis-assistant.git
cd jarvis-assistant
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
# Install Poetry if not installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install
```

#### Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

#### Database Setup
```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run migrations
poetry run alembic upgrade head
```

### 3. Frontend Setup

#### Install Node.js Dependencies
```bash
cd frontend

# Install pnpm if not installed
npm install -g pnpm

# Install dependencies
pnpm install
```

#### Environment Configuration
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 4. Browser Extension Setup

```bash
cd browser-extension

# Install dependencies
pnpm install

# Build extension
pnpm build
```

### 5. Monitoring Setup

```bash
# Start Prometheus and Grafana
docker-compose up -d prometheus grafana

# Import Grafana dashboards
./scripts/import-dashboards.sh
```

## Development

### Start Development Environment

#### Backend
```bash
# Start services
docker-compose up -d

# Start backend in development mode
poetry run python -m jarvis_assistant
```

#### Frontend
```bash
cd frontend
pnpm dev
```

#### Browser Extension
```bash
cd browser-extension
pnpm dev
```

### Running Tests

#### Backend Tests
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_system.py
```

#### Frontend Tests
```bash
cd frontend
pnpm test
```

#### Browser Extension Tests
```bash
cd browser-extension
pnpm test
```

### Code Quality

#### Linting
```bash
# Backend
poetry run flake8
poetry run mypy .

# Frontend
cd frontend
pnpm lint

# Browser Extension
cd browser-extension
pnpm lint
```

#### Formatting
```bash
# Backend
poetry run black .
poetry run isort .

# Frontend & Browser Extension
pnpm format
```

## Production Deployment

### 1. Build Images
```bash
# Build all images
docker-compose -f docker-compose.prod.yml build
```

### 2. Configure Production Environment
```bash
# Copy production environment file
cp .env.prod.example .env.prod

# Edit production configuration
nano .env.prod
```

### 3. Deploy Services
```bash
# Start production services
docker-compose -f docker-compose.prod.yml up -d
```

### 4. SSL Configuration
```bash
# Configure SSL certificates
./scripts/setup-ssl.sh

# Verify SSL configuration
./scripts/verify-ssl.sh
```

### 5. Monitoring Setup
```bash
# Configure alerting
./scripts/setup-alerts.sh

# Verify monitoring
./scripts/verify-monitoring.sh
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
1. Verify PostgreSQL is running
2. Check database credentials
3. Ensure database exists
4. Check network connectivity

#### Redis Connection Issues
1. Verify Redis is running
2. Check Redis configuration
3. Test Redis connectivity

#### Frontend Build Issues
1. Clear node_modules
2. Update Node.js version
3. Clear build cache

#### Browser Extension Issues
1. Check manifest.json
2. Verify permissions
3. Clear extension cache

### Logging

#### View Logs
```bash
# Backend logs
docker-compose logs -f backend

# Frontend logs
docker-compose logs -f frontend

# Database logs
docker-compose logs -f postgres
```

#### Log Levels
- DEBUG: Development debugging
- INFO: General information
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical failures

## Security

### SSL/TLS Configuration
1. Generate SSL certificates
2. Configure Nginx
3. Enable HSTS
4. Configure CSP

### Authentication Setup
1. Configure JWT settings
2. Set up user roles
3. Configure rate limiting
4. Enable 2FA (optional)

### Firewall Configuration
1. Configure allowed ports
2. Set up IP whitelisting
3. Enable DDoS protection

## Maintenance

### Backup Procedures
1. Database backup
2. File system backup
3. Configuration backup
4. Monitoring data backup

### Update Procedures
1. Stop services
2. Backup data
3. Update images
4. Run migrations
5. Restart services

### Health Checks
1. System monitoring
2. Service health
3. Resource usage
4. Error rates

## Support

### Getting Help
- GitHub Issues
- Documentation
- Community Forum
- Email Support

### Contributing
- Code Style Guide
- Pull Request Process
- Issue Templates
- Development Setup
