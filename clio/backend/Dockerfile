FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency manifest and only the source directories we need.
# pyproject.toml lives at the clio/ root (build context), so it is
# now accessible directly here — no requirements.txt needed.
COPY pyproject.toml .
COPY backend/ ./backend/
COPY generate_env/ ./generate_env/

# Install core + rag extras from pyproject.toml; skip test/lint/dev deps.
RUN pip install --no-cache-dir ".[rag]"

# manage.py lives inside backend/ but the entrypoint calls it from WORKDIR.
RUN cp /app/backend/manage.py /app/manage.py && \
    mkdir -p /app/evidence /app/data /app/exports /app/data/archives /app/data/audit && \
    chmod +x /app/backend/entrypoint.sh

EXPOSE 3001

CMD ["/app/backend/entrypoint.sh"]
