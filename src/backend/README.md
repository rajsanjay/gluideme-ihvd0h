# Transfer Requirements Management System - Backend Service

## Overview

The Transfer Requirements Management System backend service is a robust, scalable Django REST Framework application designed to manage and automate course transfer requirements between California community colleges and 4-year institutions. This service provides core functionality for requirement parsing, validation, and management through a RESTful API architecture.

Key Features:
- Automated transfer requirement parsing and validation
- Real-time course validation engine
- Version-controlled requirement management
- Multi-institution search capabilities
- Distributed task processing
- Comprehensive caching strategy
- Full-text and vector similarity search

## Prerequisites

Before setting up the development environment, ensure you have the following installed:

- Docker 24+ and Docker Compose V2
- Python 3.11+ with Poetry package manager
- AWS CLI configured with appropriate credentials
- Node.js 18+ for development tools
- Git for version control
- Make for development scripts

## Tech Stack

### Core Technologies
- Django 4.2+ - Web framework with REST API capabilities
- Django REST Framework 3.14+ - REST API toolkit with serialization
- Celery 5.3+ - Distributed task queue for async processing
- Redis 7.0+ - Cache layer and message broker
- PostgreSQL 14+ - Primary database with JSONB support

### Search Services
- MeiliSearch 1.3+ - Full-text search engine
- Pinecone - Vector similarity search service

### Development Tools
- AWS SDK - Cloud service integration
- PyTest - Testing framework with coverage reporting
- Black - Code formatting
- isort - Import sorting
- mypy - Static type checking
- Sentry - Error tracking and performance monitoring

## Getting Started

### Environment Setup

1. Clone the repository and set up the environment:
```bash
git clone <repository_url>
cd src/backend
cp .env.example .env
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Start development services:
```bash
docker-compose up -d
```

4. Initialize the database:
```bash
./scripts/init-db.sh
```

5. Start the development server:
```bash
./scripts/start-dev.sh
```

### Environment Variables

Configure the following environment variables in your `.env` file:

```ini
# Database Configuration
DB_NAME=trms_db
DB_USER=trms_user
DB_PASSWORD=<secure-password>
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Search Services
MEILISEARCH_HOST=http://localhost:7700
MEILISEARCH_KEY=<master-key>
PINECONE_API_KEY=<api-key>
PINECONE_ENVIRONMENT=<environment>

# AWS Services
AWS_ACCESS_KEY_ID=<access-key>
AWS_SECRET_ACCESS_KEY=<secret-key>
AWS_REGION=us-west-2
```

## Development Workflow

### Code Style and Quality

We maintain strict code quality standards using the following tools:

```bash
# Format code
poetry run black .
poetry run isort .

# Type checking
poetry run mypy .

# Run linting
poetry run flake8

# Run tests with coverage
poetry run pytest --cov=.
```

### Working with the API

The API documentation is available at:
- Development: http://localhost:8000/api/docs/
- Staging: https://api-staging.trms.edu/docs/
- Production: https://api.trms.edu/docs/

### Database Migrations

```bash
# Create new migrations
poetry run python manage.py makemigrations

# Apply migrations
poetry run python manage.py migrate

# Generate migration SQL
poetry run python manage.py sqlmigrate <app_name> <migration_number>
```

## Deployment

### Production Deployment

The service is deployed using AWS ECS with the following configuration:

1. Build and push Docker images:
```bash
docker build -t trms-api:latest .
docker push <ecr-repository-url>/trms-api:latest
```

2. Deploy using AWS CDK:
```bash
cd infrastructure
cdk deploy --require-approval never
```

### Monitoring and Logging

- Application metrics: AWS CloudWatch
- Error tracking: Sentry
- Distributed tracing: AWS X-Ray
- Log aggregation: CloudWatch Logs

## Troubleshooting

### Common Issues

1. Database Connection Errors
   - Verify PostgreSQL container status
   - Check credentials in .env file
   - Ensure database migrations are up to date

2. Celery Task Processing
   - Check Redis connection
   - Verify worker status using Flower dashboard
   - Review task logs in CloudWatch

3. Search Service Issues
   - Ensure MeiliSearch container is running
   - Verify index initialization
   - Check Pinecone API connectivity

## Maintenance

### Regular Tasks

1. Database Backups
   - Daily automated backups to S3
   - 30-day retention policy
   - Monthly backup verification

2. Log Management
   - Weekly log rotation
   - 30-day retention policy
   - Automated log analysis

3. Security Updates
   - Monthly dependency updates via Dependabot
   - Immediate security patch application
   - Quarterly security audit

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit changes with conventional commits
4. Submit a pull request with comprehensive description
5. Ensure CI/CD pipeline passes

## License

Copyright © 2023 Transfer Requirements Management System
All rights reserved.

## Support

For technical support:
- Email: support@trms.edu
- Slack: #trms-backend
- Documentation: https://docs.trms.edu