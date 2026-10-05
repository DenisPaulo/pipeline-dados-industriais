"""Consultas do painel: leem SOMENTE o schema marts do PostgreSQL."""

from __future__ import annotations

import os
from collections.abc import Iterable

import pandas as pd
import psycopg2

FONTES_VALIDAS = ("ai4i", "simulado")
MSG_MARTS_AUSENTES = (
    "As tabelas do schema **marts** ainda não existem. "
    "Rode o dbt build antes de abrir o painel:\n\n"
    "`docker compose run --rm --build dbt build`"
)


class MartsAusentesError(RuntimeError):
    """Schema ou tabela marts não encontrada (rode o dbt build)."""


def conexao_kwargs() -> dict[str, object]:
    senha = os.environ.get("POSTGRES_PASSWORD")
    if not senha:
        raise RuntimeError("POSTGRES_PASSWORD não definido. Use o arquivo .env.")
    return {
        "dbname": os.environ.get("POSTGRES_DB", "pipeline"),
        "user": os.environ.get("POSTGRES_USER", "pipeline"),
        "password": senha,
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    }


def conectar():
    return psycopg2.connect(**conexao_kwargs())


def _eh_marts_ausente(exc: BaseException) -> bool:
    texto = str(exc).lower()
    return "marts." in texto or 'schema "marts"' in texto or "does not exist" in texto


def _ler(conn, consulta: str, params: tuple | None = None) -> pd.DataFrame:
    try:
        return pd.read_sql_query(consulta, conn, params=params)
    except Exception as exc:
        if _eh_marts_ausente(exc):
            raise MartsAusentesError(MSG_MARTS_AUSENTES) from exc
        raise


def carregar_dim_maquina(conn, fontes: Iterable[str] | None = None) -> pd.DataFrame:
    """Uma linha por máquina (totais de leituras e falhas)."""
    fontes = tuple(fontes) if fontes else FONTES_VALIDAS
    consulta = """
        SELECT id_maquina, fonte, criada_em, total_leituras, total_falhas
        FROM marts.dim_maquina
        WHERE fonte = ANY(%s)
        ORDER BY total_falhas DESC, id_maquina
    """
    return _ler(conn, consulta, (list(fontes),))


def carregar_falhas_diarias(conn, fontes: Iterable[str] | None = None) -> pd.DataFrame:
    """Falhas agregadas por máquina e dia, filtradas pela fonte da dimensão."""
    fontes = tuple(fontes) if fontes else FONTES_VALIDAS
    consulta = """
        SELECT f.id_maquina, d.fonte, f.data_ref, f.qtd_falhas, f.modos_falha
        FROM marts.fct_falhas_diarias f
        JOIN marts.dim_maquina d ON d.id_maquina = f.id_maquina
        WHERE d.fonte = ANY(%s)
        ORDER BY f.data_ref, f.id_maquina
    """
    return _ler(conn, consulta, (list(fontes),))


def carregar_amostra_leituras(conn, fontes: Iterable[str] | None = None, limite: int = 200) -> pd.DataFrame:
    """Amostra das leituras (fato) para a tabela do painel."""
    fontes = tuple(fontes) if fontes else FONTES_VALIDAS
    consulta = """
        SELECT f.id_leitura, f.id_maquina, d.fonte, f.medido_em, f.tipo_produto,
               f.temperatura_ar_c, f.temperatura_processo_c, f.rotacao_rpm, f.torque_nm,
               f.desgaste_min, f.houve_falha, f.modos_falha, f.qtd_modos_falha
        FROM marts.fct_leituras f
        JOIN marts.dim_maquina d ON d.id_maquina = f.id_maquina
        WHERE d.fonte = ANY(%s)
        ORDER BY f.houve_falha DESC, f.medido_em DESC
        LIMIT %s
    """
    return _ler(conn, consulta, (list(fontes), limite))


def kpis_de_dim(dim: pd.DataFrame) -> dict[str, float]:
    """KPIs a partir de dim_maquina (já filtrada por fonte)."""
    if dim.empty:
        return {
            "maquinas": 0,
            "leituras": 0,
            "falhas": 0,
            "taxa_falha_pct": 0.0,
        }
    leituras = int(dim["total_leituras"].sum())
    falhas = int(dim["total_falhas"].sum())
    taxa = (100.0 * falhas / leituras) if leituras else 0.0
    return {
        "maquinas": int(len(dim)),
        "leituras": leituras,
        "falhas": falhas,
        "taxa_falha_pct": round(taxa, 2),
    }


def distribuicao_modos(falhas_diarias: pd.DataFrame) -> pd.DataFrame:
    """Conta cada modo individual a partir de modos_falha (ex.: 'HDF, PWF' e 'HDF; OSF').

    Em fct_falhas_diarias os conjuntos de uma leitura vêm separados por '; ' e, dentro
    de cada conjunto, os modos por ', '. Aqui separamos pelos dois e contamos cada modo.
    """
    contagem: dict[str, int] = {}
    if falhas_diarias.empty or "modos_falha" not in falhas_diarias.columns:
        return pd.DataFrame(columns=["modo", "ocorrencias"])
    for conjunto, qtd in zip(
        falhas_diarias["modos_falha"].fillna(""),
        falhas_diarias["qtd_falhas"].fillna(0).astype(int),
        strict=True,
    ):
        # Cada linha do fato diário pode misturar vários conjuntos; para a distribuição
        # usamos a presença do modo no dia (1 por linha), não a qtd_falhas.
        _ = qtd  # mantido para deixar explícito que não reponderamos por qtd aqui
        modos: set[str] = set()
        for parte in str(conjunto).split(";"):
            for modo in parte.split(","):
                m = modo.strip()
                if m:
                    modos.add(m)
        for m in modos:
            contagem[m] = contagem.get(m, 0) + 1
    if not contagem:
        return pd.DataFrame(columns=["modo", "ocorrencias"])
    out = pd.DataFrame([{"modo": k, "ocorrencias": v} for k, v in contagem.items()]).sort_values(
        "ocorrencias", ascending=False, ignore_index=True
    )
    return out


def marts_existem(conn) -> bool:
    """True se marts.dim_maquina existir (checagem barata para a UI)."""
    consulta = """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'marts' AND table_name = 'dim_maquina'
        LIMIT 1
    """
    df = pd.read_sql_query(consulta, conn)
    return not df.empty
