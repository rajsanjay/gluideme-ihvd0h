# syntax=docker/dockerfile:1.4

# Stage 1: Dependencies
FROM node:18-alpine AS deps
LABEL maintainer="Transfer Requirements Management System Team"
LABEL org.opencontainers.image.source="https://github.com/organization/repo"

WORKDIR /app

# Optimize npm for production and CI
ENV NODE_ENV=production \
    NPM_CONFIG_LOGLEVEL=warn \
    NPM_CONFIG_CI=true \
    NEXT_TELEMETRY_DISABLED=1

# Install additional dependencies required for node-gyp and sharp
RUN apk add --no-cache python3 make g++ libc6-compat

# Copy package files with layer caching
COPY package.json package-lock.json ./

# Install dependencies with strict CI mode and cache
RUN npm ci --only=production && \
    npm cache clean --force

# Stage 2: Builder
FROM node:18-alpine AS builder

WORKDIR /app

# Set build environment
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package.json ./package.json

# Copy source code (respect .dockerignore)
COPY . .

# Build arguments for runtime configuration
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_ENVIRONMENT
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_ENVIRONMENT=${NEXT_PUBLIC_ENVIRONMENT}

# Build application with optimizations
RUN npm run build && \
    # Remove unnecessary files
    rm -rf ./src/.next/cache && \
    # Optimize output
    find . -name "*.js.map" -type f -delete && \
    find . -name "*.d.ts" -type f -delete

# Stage 3: Runner
FROM node:18-alpine AS runner

WORKDIR /app

# Production environment configuration
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    NEXT_SHARP_PATH=/app/node_modules/sharp

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs && \
    chown -R nextjs:nodejs /app

# Install production-only dependencies
RUN apk add --no-cache wget curl

# Copy production artifacts
COPY --from=builder --chown=nextjs:nodejs /app/next.config.js ./
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Security hardening
RUN chmod -R 755 /app && \
    # Remove unnecessary tools
    rm -rf /var/cache/apk/* && \
    # Set strict permissions
    chmod 444 next.config.js && \
    chmod 555 public

# Switch to non-root user
USER nextjs

# Health check configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# Expose application port
EXPOSE 3000

# Set security options
LABEL security.capabilities=none
LABEL security.privileged=false

# Start the application
CMD ["node", "server.js"]

# Additional metadata
LABEL version="1.0.0"
LABEL description="Transfer Requirements Management System Frontend"
LABEL environment="${NEXT_PUBLIC_ENVIRONMENT}"