FROM python:3.11-slim


# System packages needed by psycopg2 and bcrypt
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

    WORKDIR /app


    # Install dependencies first — this layer caches
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Then copy code
COPY app/ ./app/

# Don't run as root
RUN useradd -m -u 1000 hmsuser && chown -R hmsuser:hmsuser /app
USER hmsuser


EXPOSE 8000


HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/docs || exit 1


    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
