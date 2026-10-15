"""DAG do pipeline industrial: ETL Python -> freshness -> dbt build.

- etl: roda o pipeline existente (ingestão -> limpeza -> carga no PostgreSQL).
- dbt_source_freshness: os dados foram carregados recentemente? (tabela cargas).
- dbt_build: cria staging, intermediate e marts e roda os testes do dbt (inclui volume).

Os caminhos podem ser trocados por variáveis de ambiente (os padrões são os do container).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

PIPELINE_HOME = os.environ.get("PIPELINE_HOME", "/opt/pipeline")
ETL_PYTHON = os.environ.get("ETL_PYTHON", "/home/airflow/venvs/etl/bin/python")
DBT_BIN = os.environ.get("DBT_BIN", "/home/airflow/venvs/dbt/bin/dbt")

log = logging.getLogger(__name__)


def alerta_falha(context) -> None:
    """Alerta simples: por enquanto só escreve no log. Depois pode virar e-mail/Slack."""
    ti = context.get("task_instance")
    log.error(
        "ALERTA DO PIPELINE: a task '%s' da DAG '%s' falhou (execução %s, tentativa %s). Veja o log da task.",
        getattr(ti, "task_id", "?"),
        getattr(ti, "dag_id", "?"),
        context.get("run_id", "?"),
        getattr(ti, "try_number", "?"),
    )


default_args = {
    "owner": "pipeline",
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "on_failure_callback": alerta_falha,
}

with DAG(
    dag_id="pipeline_industrial",
    description="ETL de sensores industriais e dbt build (staging, intermediate, marts)",
    schedule="@daily",
    start_date=datetime(2026, 10, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["pipeline", "etl", "dbt", "v3"],
) as dag:
    etl = BashOperator(
        task_id="etl",
        bash_command=f"cd {PIPELINE_HOME} && PYTHONPATH=src {ETL_PYTHON} -m pipeline.run",
    )

    dbt_source_freshness = BashOperator(
        task_id="dbt_source_freshness",
        bash_command=(
            f"{DBT_BIN} source freshness --project-dir {PIPELINE_HOME}/dbt"
            f" --profiles-dir {PIPELINE_HOME}/dbt --no-use-colors"
        ),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"{DBT_BIN} build --project-dir {PIPELINE_HOME}/dbt"
            f" --profiles-dir {PIPELINE_HOME}/dbt --no-use-colors"
        ),
    )

    etl >> dbt_source_freshness >> dbt_build
