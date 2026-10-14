# ==============================================================
# Dockerfile
#
# Multi-stage production image for the HR Attrition AI system.
# Build:  docker build -t hr-attrition-ai .
# Run:    docker run -p 5000:5000 hr-attrition-ai
# ==============================================================

# ── Stage 1: Build / dependency installation ──────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# System dependencies for numpy / TensorFlow compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into a venv
COPY requirements.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ── Stage 2: Production runtime ───────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Non-root user for security
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY . .

# Set ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Make venv binaries available
ENV PATH="/opt/venv/bin:$PATH"

# Application environment
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV APP_ENV=production
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Production entry point via Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--threads", "4", \
     "--worker-class", "gthread", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "app:app"]
