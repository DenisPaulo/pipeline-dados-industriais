# Airflow (V3): orquestração do pipeline

O Airflow roda o pipeline inteiro em ordem e de forma agendada:

```
etl  >>  dbt_source_freshness  >>  dbt_build
```

1. **`etl`**: roda o ETL em Python (`python -m pipeline.run`). Ele baixa/gera os dados, limpa e carrega no PostgreSQL (e registra uma linha na tabela `cargas`).
2. **`dbt_source_freshness`**: `dbt source freshness` — a última carga foi há menos de 24/48 h?
3. **`dbt_build`**: `dbt build` (modelos + testes, incluindo os de **volume**).

## Conceitos básicos

| Termo | O que é |
|---|---|
| **DAG** | O "fluxo de trabalho": a lista de tarefas e a ordem entre elas. Aqui: `pipeline_industrial`, em [`dags/pipeline_industrial.py`](dags/pipeline_industrial.py). |
| **Task (tarefa)** | Um passo do fluxo. Aqui são três: `etl`, `dbt_source_freshness` e `dbt_build`. Cada uma só roda se a anterior der certo. |
| **Scheduler** | O processo que olha o relógio e dispara a DAG na hora certa (`@daily` = uma vez por dia, à meia-noite UTC). |
| **Retry** | Nova tentativa automática quando uma tarefa falha. Aqui: até **2** novas tentativas, esperando **1 minuto** entre elas. |
| **Alerta** | Se uma tarefa falhar de vez, a função `alerta_falha` escreve uma linha `ALERTA DO PIPELINE ...` no log. |

`catchup=False`: ao ligar a DAG, o Airflow **não** tenta rodar todos os dias passados, só o próximo.

## Como funciona o container

- Um único container roda `airflow standalone` (API/UI + scheduler + dag-processor + triggerer), com **LocalExecutor**.
- Imagem oficial fixada: `apache/airflow:3.3.2-python3.12` ([`Dockerfile`](Dockerfile)).
- O ETL e o dbt ficam em ambientes Python **separados** dentro da imagem, com as mesmas versões do projeto (`requirements.txt` e `dbt/requirements.txt`), para não conflitarem com o Airflow.
- Os metadados do Airflow ficam num banco **`airflow`** no mesmo PostgreSQL do projeto. O script [`preparar.py`](preparar.py) cria esse banco na primeira subida (se já existir, não faz nada).
- O código (`src`, `sql`, `dbt`, `airflow/dags`) é montado como somente leitura: editou a DAG no Windows, o Airflow enxerga em até ~1 minuto.
- Os arquivos Parquet do ETL ficam num volume do Docker (`airflow_dados`), não na pasta `data/` do seu PC.

## Modo leve (pouca RAM)

O Airflow é configurado para gastar pouca memória (bom para notebooks e PCs com 8 GB):

| Configuração | Valor | Efeito |
|---|---|---|
| `mem_limit` do container `airflow` | `2g` (mude com `AIRFLOW_MEM_LIMIT` no `.env`) | O container nunca passa de 2 GB |
| `mem_limit` do `postgres` | `512m` (`POSTGRES_MEM_LIMIT`) | Banco limitado |
| `AIRFLOW__CORE__PARALLELISM` | `1` | Uma tarefa por vez |
| `AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG` | `1` | Idem, por DAG |
| `AIRFLOW__API__WORKERS` | `1` | Um processo só para a UI/API |
| `AIRFLOW__DAG_PROCESSOR__PARSING_PROCESSES` | `1` | Um processo lendo as DAGs |
| `AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL` / `MIN_FILE_PROCESS_INTERVAL` | `60` s | Relê as DAGs com menos frequência |
| `AIRFLOW__CORE__LOAD_EXAMPLES` | `False` | Sem DAGs de exemplo |

**RAM necessária:** reserve **~2 GB livres** para o Airflow (o Docker Desktop no Windows deve ter pelo menos ~4 GB no total). Não precisa subir o painel ao mesmo tempo.

## Passo a passo (Windows + Git Bash)

Pré-requisito: Docker Desktop aberto.

```bash
cd "/i/Nova pasta/pipeline-dados-industriais"

# 1) .env: se ainda não tem, copie do exemplo. Depois edite as senhas.
cp -n .env.example .env
#    Confira se existem as linhas AIRFLOW_ADMIN_USER e AIRFLOW_ADMIN_PASSWORD
#    (se o seu .env é antigo, copie essas duas linhas do .env.example).

# 2) Subir (a primeira vez demora: baixa a imagem e instala ETL + dbt)
docker compose --profile airflow up -d --build airflow
#    ou: make airflow

# 3) Acompanhar até aparecer "healthy"
docker compose ps
```

Abra **http://localhost:8080** e entre com `AIRFLOW_ADMIN_USER` / `AIRFLOW_ADMIN_PASSWORD` do seu `.env`.

### Rodar a DAG

Pela UI: abra `pipeline_industrial`, ligue o botão (a DAG começa **pausada**) e clique em **Trigger**.

Pelo terminal:

```bash
docker compose exec airflow airflow dags unpause pipeline_industrial
docker compose exec airflow airflow dags trigger pipeline_industrial

# Ou: roda a DAG inteira na hora, mostrando o log no terminal (não precisa da UI)
docker compose exec airflow airflow dags test pipeline_industrial
```

> No Git Bash, se aparecer erro de caminho (`C:/Program Files/Git/...`), rode com `MSYS_NO_PATHCONV=1` na frente do comando.

### Ver logs

- Na UI: clique na execução → na tarefa (`etl` ou `dbt_build`) → aba **Logs**.
- No terminal: `docker compose logs -f airflow`.

### Parar

```bash
docker compose --profile airflow down   # ou: make airflow-down
```

Os dados e o histórico do Airflow ficam nos volumes. Para apagar tudo: `docker compose --profile airflow down -v` (cuidado: apaga também o banco do projeto).
