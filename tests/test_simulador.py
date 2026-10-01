import pandas as pd

from pipeline.schemas import COLUNAS_BRUTO
from pipeline.simulador import gerar_leituras

PEQUENO = dict(n_maquinas=3, dias=1, intervalo_min=10)


def test_mesma_semente_gera_saida_identica():
    a, ra = gerar_leituras(semente=7, **PEQUENO)
    b, rb = gerar_leituras(semente=7, **PEQUENO)
    pd.testing.assert_frame_equal(a, b)
    assert ra == rb


def test_sementes_diferentes_geram_saidas_diferentes():
    a, _ = gerar_leituras(semente=1, **PEQUENO)
    b, _ = gerar_leituras(semente=2, **PEQUENO)
    assert not a.equals(b)


def test_estrutura_e_series_por_maquina():
    df, resumo = gerar_leituras(semente=3, **PEQUENO)
    assert list(df.columns) == COLUNAS_BRUTO
    assert sorted(df["maquina_id"].unique()) == ["SIM-01", "SIM-02", "SIM-03"]
    assert resumo["linhas_base"] == 3 * 144
    assert len(df) == resumo["linhas_total"] == resumo["linhas_base"] + resumo["duplicadas"]


def test_problemas_sao_injetados_de_verdade():
    df, resumo = gerar_leituras(semente=42, n_maquinas=4, dias=3, intervalo_min=5)
    assert resumo["nulos"] > 0 and resumo["outliers"] > 0 and resumo["lixo"] > 0 and resumo["duplicadas"] > 0
    assert df["torque_nm"].isna().any()
    assert (df["temp_ar_k"] == "ERRO").any() or (df["torque_nm"] == "ERRO").any()
