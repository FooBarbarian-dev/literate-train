FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies first for layer caching.
# tomllib (stdlib since 3.11) reads pyproject.toml directly so this layer
# is only invalidated when pyproject.toml changes, not on source changes.
COPY pyproject.toml .
RUN python3 - <<'EOF'
import tomllib, subprocess, sys
with open("pyproject.toml", "rb") as f:
    t = tomllib.load(f)
extras = t["project"].get("optional-dependencies", {})
deps = t["project"]["dependencies"] + extras.get("rag", [])
subprocess.run(
    [sys.executable, "-m", "pip", "install", "--no-cache-dir"] + deps,
    check=True,
)
EOF

# Copy only the source directories we need, then install the package itself.
# --no-deps is fast here because all dependencies are already in the layer above.
COPY backend/ ./backend/
COPY generate_env/ ./generate_env/
RUN pip install --no-cache-dir --no-deps .

# manage.py lives inside backend/ but the entrypoint calls it from WORKDIR.
RUN cp /app/backend/manage.py /app/manage.py && \
    mkdir -p /app/evidence /app/data /app/exports /app/data/archives /app/data/audit && \
    chmod +x /app/backend/entrypoint.sh

# Pre-download the sentence-transformers embedding model so it's baked into
# the image and available without internet access at runtime.  The celery_worker
# runs the RAG retriever; if this model is missing at task time, get_retriever()
# silently falls back to _EmptyRetriever and the assistant gets no context.
# SENTENCE_TRANSFORMERS_HOME pins the cache to a predictable path so both
# the backend and celery_worker containers (same image) find the same files.
ENV SENTENCE_TRANSFORMERS_HOME=/app/models/sentence_transformers
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('BAAI/bge-small-en-v1.5'); \
print('Embedding model cached.')"

EXPOSE 3001

CMD ["/app/backend/entrypoint.sh"]
