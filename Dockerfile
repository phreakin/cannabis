FROM python:3.12-slim

WORKDIR /app

# System utilities — curl required by HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies — own layer so code changes don't invalidate the cache
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt \
    && pip install --no-cache-dir --only-binary :all: pandas numpy

# Application source
COPY . .

# Create non-root user and ensure runtime directories exist
RUN useradd -m -u 1000 appuser \
    && mkdir -p data/raw data/processed data/export data/triggers logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "main.py"]
