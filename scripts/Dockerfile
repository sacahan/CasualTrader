# ============================================
# Multi-stage Docker Build for CasualTrader
# ============================================
# Stage 0: MCP Source
FROM alpine/git AS mcp-source

WORKDIR /opt

RUN git clone --depth 1 https://github.com/sacahan/CasualMarket.git casual-market-mcp

# Stage 1: Frontend Build
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Clean up package-lock.json to avoid npm optional dependency issues
# Then install all dependencies (including dev dependencies for build)
RUN rm -f package-lock.json && npm install

# Copy frontend source
COPY frontend/ ./

# Build frontend static files with production API URL
ENV VITE_API_BASE_URL=https://trader.brianhan.cc
ENV VITE_WS_URL=wss://trader.brianhan.cc/ws
RUN npm run build

# ============================================
# Stage 2: Backend Build
FROM python:3.12-slim AS backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements
COPY backend/pyproject.toml ./

# Install uv for faster Python package management
RUN pip install --no-cache-dir uv

# Install Python dependencies from pyproject.toml
RUN uv pip install --system --no-cache .

# Copy MCP source into build stage and install its dependencies
COPY --from=mcp-source /opt/casual-market-mcp /tmp/casual-market-mcp
RUN uv pip install --system --no-cache /tmp/casual-market-mcp

# ============================================
# Stage 3: Production Image
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy backend source
COPY backend/src ./src
COPY backend/run_server.py ./

# Copy frontend build (static files)
COPY --from=frontend-builder /frontend/dist ./static

# Copy MCP source repository
COPY --from=mcp-source /opt/casual-market-mcp /app/mcp/casual-market-mcp

# Create necessary directories
RUN mkdir -p /app/logs /app/memory /app/custom_logs /app/mcp

# Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV STATIC_DIR=/app/static

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["python", "run_server.py"]
