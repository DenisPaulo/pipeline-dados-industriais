"""Carga idempotente no PostgreSQL.

Estratégia: COPY para tabelas temporárias (rápido) e depois ``INSERT ... ON CONFLICT`` nas
tabelas finais. Rodar duas vezes com os mesmos dados não duplica nada: a chave natural de
``leituras`` é (maquina_id, ts) e a de ``falhas`` é (leitura_id, modo). Tudo em uma transação:
se algo falhar, nada é gravado.
"""

from __future__ import annotations

import io
import time
from pathlib import Path

import pandas as pd
import psycopg2

from .config import Config

COLUNAS_LEITURAS = [
    "maquina_id", "fonte", "ts", "tipo_produto", "temp_ar_k", "temp_processo_k",
    "rotacao_rpm", "torque_nm", "desgaste_min", "falha",
]  # fmt: skip
COLUNAS_FALHAS = ["maquina_id", "ts", "modo"]

SQL_STAGING = """
CREATE TEMP TABLE stg_leituras (
    maquina_id TEXT, fonte TEXT, ts TIMESTAMP, tipo_produto CHAR(1), temp_ar_k DOUBLE PRECISION,
    temp_processo_k DOUBLE PRECISION, rotacao_rpm INTEGER, torque_nm DOUBLE PRECISION,
    desgaste_min INTEGER, falha BOOLEAN
) ON COMMIT DROP;
CREATE TEMP TABLE stg_falhas (maquina_id TEXT, ts TIMESTAMP, modo TEXT) ON COMMIT DROP;
"""

SQL_MAQUINAS = """
INSERT INTO maquinas (maquina_id, fonte)
SELECT DISTINCT maquina_id, fonte FROM stg_leituras
ON CONFLICT (maquina_id) DO NOTHING;
"""

# (xmax = 0) é verdadeiro só para linhas realmente inseridas; as demais foram atualizadas.
SQL_LEITURAS = """
WITH r AS (
    INSERT INTO leituras (maquina_id, ts, tipo_produto, temp_ar_k, temp_processo_k,
                          rotacao_rpm, torque_nm, desgaste_min, falha)
    SELECT maquina_id, ts, tipo_produto, temp_ar_k, temp_processo_k,
           rotacao_rpm, torque_nm, desgaste_min, falha
    FROM stg_leituras
    ON CONFLICT (maquina_id, ts) DO UPDATE SET
        tipo_produto = EXCLUDED.tipo_produto, temp_ar_k = EXCLUDED.temp_ar_k,
        temp_processo_k = EXCLUDED.temp_processo_k, rotacao_rpm = EXCLUDED.rotacao_rpm,
        torque_nm = EXCLUDED.torque_nm, desgaste_min = EXCLUDED.desgaste_min,
        falha = EXCLUDED.falha
    WHERE (leituras.tipo_produto, leituras.temp_ar_k, leituras.temp_processo_k,
           leituras.rotacao_rpm, leituras.torque_nm, leituras.desgaste_min, leituras.falha)
          IS DISTINCT FROM
          (EXCLUDED.tipo_produto, EXCLUDED.temp_ar_k, EXCLUDED.temp_processo_k,
           EXCLUDED.rotacao_rpm, EXCLUDED.torque_nm, EXCLUDED.desgaste_min, EXCLUDED.falha)
    RETURNING (xmax = 0) AS inserida
)
SELECT count(*) FILTER (WHERE inserida), count(*) FILTER (WHERE NOT inserida) FROM r;
"""

# Remove falhas que existem no banco para as leituras carregadas mas não estão mais nos dados.
SQL_FALHAS_REMOVER = """
DELETE FROM falhas f USING leituras l, (SELECT DISTINCT maquina_id, ts FROM stg_leituras) s
WHERE f.leitura_id = l.leitura_id AND l.maquina_id = s.maquina_id AND l.ts = s.ts
  AND NOT EXISTS (SELECT 1 FROM stg_falhas g
                  WHERE g.maquina_id = l.maquina_id AND g.ts = l.ts AND g.modo = f.modo);
"""

SQL_FALHAS = """
WITH r AS (
    INSERT INTO falhas (leitura_id, modo)
    SELECT l.leitura_id, g.modo
    FROM stg_falhas g JOIN leituras l ON l.maquina_id = g.maquina_id AND l.ts = g.ts
    ON CONFLICT (leitura_id, modo) DO NOTHING
    RETURNING 1
)
SELECT count(*) FROM r;
"""


def para_csv(df: pd.DataFrame, colunas: list[str]) -> io.StringIO:
    """Serializa o DataFrame em CSV (sem cabeçalho) no formato esperado pelo COPY."""
    buf = io.StringIO()
    out = df[colunas].copy()
    if "ts" in out:
        out["ts"] = out["ts"].dt.strftime("%Y-%m-%d %H:%M:%S")
    if "falha" in out:
        out["falha"] = out["falha"].map({True: "t", False: "f"})
    out.to_csv(buf, index=False, header=False)
    buf.seek(0)
    return buf


def conectar(cfg: Config, tentativas: int = 30, espera_s: float = 2.0):
    """Conecta ao PostgreSQL, esperando o banco ficar pronto (útil logo após ``docker compose up``)."""
    kwargs = cfg.conexao_kwargs()
    for i in range(1, tentativas + 1):
        try:
            return psycopg2.connect(**kwargs)
        except psycopg2.OperationalError as exc:
            if i == tentativas:
                raise
            print(f"[carga] banco indisponível ({i}/{tentativas}): {str(exc).strip()[:80]}")
            time.sleep(espera_s)
    raise AssertionError("inalcançável")


def aplicar_schema(conn, schema_path: Path) -> None:
    with conn.cursor() as cur:
        cur.execute(schema_path.read_text(encoding="utf-8"))
    conn.commit()


def carregar(conn, leituras: pd.DataFrame, falhas: pd.DataFrame) -> dict[str, int]:
    """Carrega leituras e falhas numa única transação. Retorna contagens do que mudou."""
    try:
        with conn.cursor() as cur:
            cur.execute(SQL_STAGING)
            cur.copy_expert(
                f"COPY stg_leituras ({', '.join(COLUNAS_LEITURAS)}) FROM STDIN WITH (FORMAT csv)",
                para_csv(leituras, COLUNAS_LEITURAS),
            )
            cur.copy_expert(
                f"COPY stg_falhas ({', '.join(COLUNAS_FALHAS)}) FROM STDIN WITH (FORMAT csv)",
                para_csv(falhas, COLUNAS_FALHAS),
            )
            cur.execute(SQL_MAQUINAS)
            maquinas_novas = cur.rowcount
            cur.execute(SQL_LEITURAS)
            inseridas, atualizadas = cur.fetchone()
            cur.execute(SQL_FALHAS_REMOVER)
            falhas_removidas = cur.rowcount
            cur.execute(SQL_FALHAS)
            (falhas_novas,) = cur.fetchone()
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return {
        "maquinas_novas": maquinas_novas,
        "leituras_inseridas": int(inseridas),
        "leituras_atualizadas": int(atualizadas),
        "falhas_inseridas": int(falhas_novas),
        "falhas_removidas": falhas_removidas,
    }


def contagens(conn) -> dict[str, int]:
    with conn.cursor() as cur:
        out = {}
        for tabela in ("maquinas", "leituras", "falhas"):
            cur.execute(f"SELECT count(*) FROM {tabela}")  # nomes fixos, sem entrada externa
            out[tabela] = cur.fetchone()[0]
    return out
