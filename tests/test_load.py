"""Testes da carga SEM PostgreSQL: serialização para COPY e coerência do schema.sql."""

import re
from pathlib import Path

import pandas as pd

from pipeline.clean import limpar
from pipeline.load import COLUNAS_FALHAS, COLUNAS_LEITURAS, SQL_LEITURAS, para_csv
from pipeline.schemas import FAIXAS_FISICAS, MODOS_FALHA
from tests.conftest import linha, quadro

SCHEMA = (Path(__file__).resolve().parents[1] / "sql" / "schema.sql").read_text(encoding="utf-8")


def test_para_csv_formato_do_copy():
    leituras, falhas, _, _ = limpar(quadro(linha(falha="1", modo_falha="TWF")))
    saida = para_csv(leituras, COLUNAS_LEITURAS).read().strip()
    assert saida == "M-01,simulado,2026-01-01 00:00:00,L,300.0,310.0,1500,40.0,10,t"
    assert para_csv(falhas, COLUNAS_FALHAS).read().strip() == "M-01,2026-01-01 00:00:00,TWF"


def test_para_csv_nao_altera_o_dataframe():
    leituras, _, _, _ = limpar(quadro(linha()))
    antes = leituras.copy(deep=True)
    para_csv(leituras, COLUNAS_LEITURAS)
    pd.testing.assert_frame_equal(leituras, antes)


def test_schema_tem_tabelas_chaves_e_indices():
    for tabela in ("maquinas", "leituras", "falhas"):
        assert re.search(rf"CREATE TABLE IF NOT EXISTS {tabela}\b", SCHEMA)
    assert "PRIMARY KEY" in SCHEMA and "REFERENCES maquinas" in SCHEMA and "REFERENCES leituras" in SCHEMA
    assert "UNIQUE (maquina_id, ts)" in SCHEMA  # base da idempotência
    assert len(re.findall(r"CREATE INDEX IF NOT EXISTS", SCHEMA)) >= 3


def test_schema_espelha_as_faixas_fisicas_do_codigo():
    for coluna, (lo, hi) in FAIXAS_FISICAS.items():
        assert f"{coluna} BETWEEN {lo:g} AND {hi:g}" in SCHEMA.replace("  ", " ")


def test_schema_aceita_todos_os_modos_de_falha():
    for modo in [*MODOS_FALHA, "DESCONHECIDO"]:
        assert f"'{modo}'" in SCHEMA


def test_upsert_usa_a_chave_natural():
    assert "ON CONFLICT (maquina_id, ts)" in SQL_LEITURAS
