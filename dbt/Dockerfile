# Imagem do dbt (V2). O projeto em si NÃO é copiado: o docker-compose monta a pasta dbt/ em /dbt,
# então editar um modelo não exige reconstruir a imagem.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DBT_PROFILES_DIR=/dbt \
    DBT_PROJECT_DIR=/dbt

# git: o `dbt debug` verifica se ele existe (o dbt usa git para baixar pacotes)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /dbt

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Usuário sem privilégios
RUN useradd --create-home --uid 1000 dbt
USER dbt

# `docker compose run --rm dbt build` => `dbt build`
ENTRYPOINT ["dbt"]
CMD ["--help"]
