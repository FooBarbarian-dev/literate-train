FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY relation_service_cli.py .
COPY manage.py .

# Install the package (just deps first for caching)
RUN pip install --no-cache-dir .

COPY . .

RUN mkdir -p /app/data /app/logs

EXPOSE 3002

CMD ["clio-relation-server"]
