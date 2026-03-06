# ─────────────────────────────────────────────────────────────
# DOCKERFILE — Django Backend
#
# Multi-stage thinking:
#   Stage 1 (builder): install Python deps in an isolated layer
#   Stage 2 (runtime): copy only what's needed — keeps image small
#
# WHY ALPINE? Smaller image (~50MB vs ~900MB for full Ubuntu).
# Tradeoff: some C-extension packages need extra build deps.
# ─────────────────────────────────────────────────────────────

FROM python:3.12-slim

# Prevents Python from writing .pyc files (bytecode cache)
# and ensures stdout/stderr are sent straight to terminal (no buffering)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed by psycopg2 (Postgres driver)
# and Pillow (image processing for profile pictures)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements FIRST — Docker caches this layer.
# If requirements don't change, Docker won't re-install them on rebuild.
# This is a key performance trick for fast rebuilds.
COPY requirements/ requirements/
RUN pip install --upgrade pip && \
    pip install -r requirements/dev.txt

# Copy the rest of the source code
COPY . .

# Create a non-root user for security (never run as root in containers!)
RUN addgroup --system django && adduser --system --group django
USER django

EXPOSE 8000
