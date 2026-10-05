.PHONY: help install up down run run-local dbt-debug dbt-build painel test test-integration lint format queries psql clean

PY ?= python
COMPOSE ?= docker compose

help: ## Lista os comandos
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  make %-18s %s\n", $$1, $$2}'

install: ## Instala as dependências de desenvolvimento
	$(PY) -m pip install -r requirements-dev.txt

up: ## Sobe o PostgreSQL (docker compose) e espera ficar saudável
	@test -f .env || { echo "Crie o .env: cp .env.example .env (e defina POSTGRES_PASSWORD)"; exit 1; }
	$(COMPOSE) up -d --wait postgres

down: ## Derruba os serviços (mantém o volume do banco)
	$(COMPOSE) down

run: up ## Roda o pipeline completo dentro do Docker (ingestão -> limpeza -> carga)
	$(COMPOSE) run --rm --build app

dbt-debug: up ## dbt: testa a conexão com o banco (V2)
	$(COMPOSE) run --rm --build dbt debug

dbt-build: up ## dbt: cria os modelos e roda os testes (V2; rode `make run` antes)
	$(COMPOSE) run --rm --build dbt build

painel: up ## Sobe o painel Streamlit (http://localhost:8501); rode make dbt-build antes
	$(COMPOSE) --profile painel up -d --build painel

run-local: ## Roda o pipeline no host (exige banco acessível e variáveis POSTGRES_* no ambiente)
	PYTHONPATH=src $(PY) -m pipeline.run

test: ## Testes rápidos: sem rede e sem PostgreSQL
	$(PY) -m pytest -q

test-integration: ## Testes que usam um PostgreSQL real (variáveis POSTGRES_* no ambiente)
	$(PY) -m pytest -q -m integration

lint: ## ruff: lint e verificação de formatação
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

format: ## Formata o código com ruff
	$(PY) -m ruff check --fix .
	$(PY) -m ruff format .

queries: ## Executa sql/queries.sql no PostgreSQL do compose
	$(COMPOSE) exec -T postgres sh -c 'psql -U "$$POSTGRES_USER" "$$POSTGRES_DB"' < sql/queries.sql

psql: ## Abre um psql interativo no PostgreSQL do compose
	$(COMPOSE) exec postgres sh -c 'psql -U "$$POSTGRES_USER" "$$POSTGRES_DB"'

clean: ## Remove dados gerados (data/raw e data/processed) — não mexe no banco
	rm -rf data/raw data/processed/bruto data/processed/limpo data/processed/relatorio.json
