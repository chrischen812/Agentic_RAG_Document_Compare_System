# Multi-stage build for Agentic RAG System
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./
COPY uv.lock ./

# Install UV package manager for faster dependency resolution
RUN pip install uv

# Install Python dependencies
RUN uv pip install --system -r pyproject.toml

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appuser && useradd -r -g appuser appuser

# Copy Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create app directory and set ownership
WORKDIR /app
RUN chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser ontologies/ ./ontologies/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser main.py ./
COPY --chown=appuser:appuser pyproject.toml ./

# Create data directory for persistent storage
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run the application
CMD ["python", "main.py"]