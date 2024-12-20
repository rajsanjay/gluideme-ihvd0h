# Stage 1: Build initialization scripts
FROM alpine:3.18 AS script-builder
# @version 3.18 - Alpine Linux base image for initialization scripts

# Install required utilities
RUN apk add --no-cache \
    bash~=5.2 \
    curl~=8.1 \
    jq~=1.6

# Create script directory
WORKDIR /scripts

# Copy initialization scripts
COPY scripts/init.sh /scripts/
COPY scripts/healthcheck.sh /scripts/

# Set proper permissions
RUN chmod +x /scripts/*.sh

# Stage 2: Production MeiliSearch
FROM getmeili/meilisearch:v1.3
# @version v1.3 - Production MeiliSearch base image

# Labels for container identification and maintenance
LABEL maintainer="Transfer Requirements Management System" \
      description="Production MeiliSearch instance for transfer requirements search" \
      version="1.0"

# Environment variables for production configuration
ENV MEILI_HTTP_ADDR=0.0.0.0:7700 \
    MEILI_ENV=production \
    MEILI_NO_ANALYTICS=true \
    MEILI_DB_PATH=/meili_data \
    MEILI_MAX_INDEXING_MEMORY=2GB \
    MEILI_MAX_INDEXING_THREADS=4 \
    MEILI_HTTP_PAYLOAD_SIZE_LIMIT=100MB

# Create necessary directories with proper permissions
RUN mkdir -p /meili_data /etc/meilisearch /scripts \
    && chown -R meilisearch:meilisearch /meili_data /etc/meilisearch

# Copy initialization scripts from builder
COPY --from=script-builder /scripts/ /scripts/
RUN chmod +x /scripts/*.sh

# Copy configuration file
COPY config.toml /etc/meilisearch/config.toml

# System optimizations for production
RUN ulimit -n 65535 \
    && sysctl -w vm.max_map_count=262144 || true

# Expose ports for API and metrics
EXPOSE 7700 7701

# Volume configuration for persistence and configuration
VOLUME ["/meili_data", "/etc/meilisearch"]

# Health check configuration
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=40s \
    CMD /scripts/healthcheck.sh

# Switch to non-root user for security
USER meilisearch

# Enhanced entrypoint with initialization
ENTRYPOINT ["/scripts/init.sh"]

# Default command to start MeiliSearch
CMD ["meilisearch", "--config", "/etc/meilisearch/config.toml"]