FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data /app/logs

EXPOSE 3002

CMD ["gunicorn", "relation_service.asgi:application", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:3002"]
