FROM python:3.14-slim

# Install system updates and runtime dependencies in single layer
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies with build tools, then remove build deps
COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        build-essential && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y gcc build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application code and database
COPY app/ ./app/
COPY data/aircraft.db ./data/aircraft.db

# Set environment variables
ENV PYTHONPATH=/app/app \
    DB_PATH=/app/data/aircraft.db \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Healthcheck using curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

# Run as non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
