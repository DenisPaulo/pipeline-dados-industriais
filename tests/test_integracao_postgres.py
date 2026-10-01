"""Testes de integração com PostgreSQL real. Opcionais: só rodam com `pytest -m integration`
e com POSTGRES_PASSWORD (e, se necessário, POSTGRES_HOST/PORT/DB/USER) no ambiente.

Cada teste usa um schema temporário próprio e o remove ao final.
"""

import uuid
from pathlib import Path

import pytest

from pipeline import load
from pipeline.clean import limpar
from pipeline.config import Config
from tests.conftest import linha, quadro

pytestmark = pytest.mark.integration

SCHEMA_SQL = Path(__file__).resolve().parents[1] / "sql" / "schema.sql"


@pytest.fixture
def conn():
    cfg = Config.do_ambiente()
    if not cfg.db_senha:
        pytest.skip("POSTGRES_PASSWORD não definido")
    c = load.conectar(cfg, tentativas=3, espera_s=1)
    nome = f"teste_{uuid.uuid4().hex[:8]}"
    with c.cursor() as cur:
        cur.execute(f"CREATE SCHEMA {nome}; SET search_path TO {nome}")
    c.commit()
    yield c
    c.rollback()
    with c.cursor() as cur:
        cur.execute(f"DROP SCHEMA {nome} CASCADE")
    c.commit()
    c.close()


def dados():
    bruto = quadro(
        linha(timestamp="2026-01-01 00:00:00"),
        linha(timestamp="2026-01-01 00:05:00", falha="1", modo_falha="HDF|PWF"),
        linha(maquina_id="M-02", timestamp="2026-01-01 00:00:00", falha="1"),
    )
    leituras, falhas, _, _ = limpar(bruto)
    return leituras, falhas


def test_carga_idempotente(conn):
    load.aplicar_schema(conn, SCHEMA_SQL)
    leituras, falhas = dados()
    r1 = load.carregar(conn, leituras, falhas)
    assert r1["leituras_inseridas"] == 3 and r1["falhas_inseridas"] == 3 and r1["maquinas_novas"] == 2
    assert load.contagens(conn) == {"maquinas": 2, "leituras": 3, "falhas": 3}
    r2 = load.carregar(conn, leituras, falhas)
    assert r2["leituras_inseridas"] == 0 and r2["leituras_atualizadas"] == 0 and r2["falhas_inseridas"] == 0
    assert load.contagens(conn) == {"maquinas": 2, "leituras": 3, "falhas": 3}


def test_reprocessamento_atualiza_e_remove_falha_obsoleta(conn):
    load.aplicar_schema(conn, SCHEMA_SQL)
    leituras, falhas = dados()
    load.carregar(conn, leituras, falhas)
    leituras2 = leituras.copy()
    leituras2.loc[0, "torque_nm"] = 41.5
    falhas2 = falhas[falhas["modo"] != "PWF"]
    r = load.carregar(conn, leituras2, falhas2)
    assert r["leituras_atualizadas"] == 1 and r["falhas_removidas"] == 1
    assert load.contagens(conn)["falhas"] == 2


def test_constraint_rejeita_valor_fora_da_faixa_e_faz_rollback(conn):
    load.aplicar_schema(conn, SCHEMA_SQL)
    leituras, falhas = dados()
    ruim = leituras.copy()
    ruim.loc[1, "torque_nm"] = 999.0
    with pytest.raises(Exception, match="check"):
        load.carregar(conn, ruim, falhas)
    assert load.contagens(conn) == {"maquinas": 0, "leituras": 0, "falhas": 0}
