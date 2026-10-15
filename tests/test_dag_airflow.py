"""Teste leve da DAG do Airflow: importa sem erros e tem a ordem etl >> dbt_source_freshness >> dbt_build.

Pulado se o Airflow não estiver instalado (o CI de testes rápidos não instala o Airflow).
"""

from __future__ import annotations

from pathlib import Path

import pytest

# "airflow.models" (e não só "airflow"): a pasta airflow/ do repo seria importada como pacote vazio
pytest.importorskip("airflow.models")

from airflow.models import DagBag  # noqa: E402

PASTA_DAGS = Path(__file__).resolve().parents[1] / "airflow" / "dags"


def test_dag_importa_sem_erros_e_ordem_das_tasks():
    bag = DagBag(dag_folder=str(PASTA_DAGS), include_examples=False)
    assert bag.import_errors == {}
    dag = bag.get_dag("pipeline_industrial")
    assert dag is not None
    assert set(dag.task_ids) == {"etl", "dbt_source_freshness", "dbt_build"}
    assert dag.get_task("etl").downstream_task_ids == {"dbt_source_freshness"}
    assert dag.get_task("dbt_source_freshness").downstream_task_ids == {"dbt_build"}
    assert dag.get_task("dbt_build").retries == 2
    assert dag.catchup is False
