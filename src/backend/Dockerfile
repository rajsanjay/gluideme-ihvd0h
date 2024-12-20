# Stage 1: Builder
FROM python:3.11-slim AS builder

# Set build-time environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /build

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python build tools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt \
    && find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Stage 2: Production
FROM python:3.11-slim

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings.production \
    GUNICORN_WORKERS=4 \
    GUNICORN_THREADS=2 \
    APP_HOME=/app \
    PORT=8000 \
    WORKER_TIMEOUT=120 \
    MAX_REQUESTS=10000 \
    MAX_REQUESTS_JITTER=1000

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create app user
RUN groupadd -r appgroup && useradd -r -g appgroup appuser \
    && mkdir -p ${APP_HOME} \
    && mkdir -p /var/log/django \
    && mkdir -p /var/www/static \
    && mkdir -p /var/www/media \
    && chown -R appuser:appgroup ${APP_HOME} \
    && chown -R appuser:appgroup /var/log/django \
    && chown -R appuser:appgroup /var/www

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR ${APP_HOME}

# Copy application code and scripts
COPY --chown=appuser:appgroup . ${APP_HOME}/
COPY --chown=appuser:appgroup scripts/entrypoint.sh /usr/local/bin/
COPY --chown=appuser:appgroup scripts/start-prod.sh /usr/local/bin/

# Set correct permissions
RUN chmod 755 /usr/local/bin/entrypoint.sh \
    && chmod 755 /usr/local/bin/start-prod.sh \
    && chmod -R 755 ${APP_HOME}/scripts

# Configure health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8000/health || exit 1

# Set resource limits
ENV GUNICORN_CMD_ARGS="--workers=${GUNICORN_WORKERS} --threads=${GUNICORN_THREADS} --worker-class=gthread --worker-tmp-dir=/dev/shm --max-requests=${MAX_REQUESTS} --max-requests-jitter=${MAX_REQUESTS_JITTER}"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Set entrypoint and default command
ENTRYPOINT ["entrypoint.sh"]
CMD ["start-prod.sh"]