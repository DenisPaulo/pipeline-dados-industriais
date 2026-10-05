"""Testes das funções puras do painel (sem PostgreSQL nem Streamlit)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd
import pytest

PAINEL_DB = Path(__file__).resolve().parents[1] / "painel" / "db.py"


@pytest.fixture(scope="module")
def pdb():
    spec = importlib.util.spec_from_file_location("painel_db", PAINEL_DB)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_kpis_de_dim_vazio(pdb):
    k = pdb.kpis_de_dim(pd.DataFrame(columns=["total_leituras", "total_falhas"]))
    assert k == {"maquinas": 0, "leituras": 0, "falhas": 0, "taxa_falha_pct": 0.0}


def test_kpis_de_dim_soma_e_taxa(pdb):
    dim = pd.DataFrame(
        {
            "id_maquina": ["A", "B"],
            "total_leituras": [100, 50],
            "total_falhas": [10, 5],
        }
    )
    k = pdb.kpis_de_dim(dim)
    assert k["maquinas"] == 2
    assert k["leituras"] == 150
    assert k["falhas"] == 15
    assert k["taxa_falha_pct"] == 10.0


def test_distribuicao_modos_separa_virgula_e_ponto_e_virgula(pdb):
    diarias = pd.DataFrame(
        {
            "modos_falha": ["HDF, PWF", "HDF; OSF", "TWF"],
            "qtd_falhas": [2, 1, 3],
        }
    )
    out = pdb.distribuicao_modos(diarias)
    assert list(out.columns) == ["modo", "ocorrencias"]
    mapa = dict(zip(out["modo"], out["ocorrencias"], strict=True))
    assert mapa["HDF"] == 2  # aparece em duas linhas-dia
    assert mapa["PWF"] == 1
    assert mapa["OSF"] == 1
    assert mapa["TWF"] == 1


def test_distribuicao_modos_vazio(pdb):
    out = pdb.distribuicao_modos(pd.DataFrame())
    assert out.empty
