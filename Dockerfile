FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY sql ./sql

# Usuário sem privilégios; /app/data é um volume montado pelo docker compose
RUN useradd --create-home --uid 1000 pipeline && mkdir -p /app/data && chown -R pipeline /app/data
USER pipeline

CMD ["python", "-m", "pipeline.run"]
