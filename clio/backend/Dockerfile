FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY cli.py .
COPY manage.py .

# Install the package in editable-like mode (just deps first for caching)
RUN pip install --no-cache-dir .

COPY . .

RUN mkdir -p /app/evidence /app/data /app/exports /app/data/archives /app/data/audit /app/data/logs

EXPOSE 3001

CMD ["clio-server"]
