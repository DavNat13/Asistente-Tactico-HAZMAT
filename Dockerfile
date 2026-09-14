# syntax=docker/dockerfile:1

FROM python:3.14-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=7.88.1-10+deb12u5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-heavy.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements-heavy.txt

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY app.py .
COPY styles/ styles/

RUN adduser --disabled-password --no-create-home appuser
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
