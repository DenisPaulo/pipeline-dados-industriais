import pandas as pd

from pipeline.ingest import (
    AI4I_MAQUINAS_VIRTUAIS,
    gravar_bruto,
    ler_ai4i,
    ler_bruto,
)
from pipeline.schemas import COLUNAS_BRUTO
from tests.conftest import linha, quadro

CABECALHO = ",".join(
    [
        "UDI", "Product ID", "Type", "Air temperature [K]", "Process temperature [K]",
        "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]", "Machine failure",
        "TWF", "HDF", "PWF", "OSF", "RNF",
    ]
)  # fmt: skip
CSV_AI4I = (
    CABECALHO
    + """
1,M14860,M,298.1,308.6,1551,42.8,0,0,0,0,0,0,0
2,L47181,L,298.2,308.7,1408,46.3,3,1,0,1,1,0,0
3,L47182,L,298.1,308.5,1498,49.4,5,1,0,0,0,0,0
11,L47190,L,298.0,308.4,1500,40.0,7,0,0,0,0,0,0
"""
)


def test_ler_ai4i_mapeia_colunas_e_maquinas_virtuais(tmp_path):
    csv = tmp_path / "ai4i2020.csv"
    csv.write_text(CSV_AI4I)
    df = ler_ai4i(csv)
    assert list(df.columns) == COLUNAS_BRUTO
    assert df["maquina_id"].tolist() == ["AI4I-01", "AI4I-02", "AI4I-03", "AI4I-01"]
    assert df["timestamp"].tolist()[0] == "2020-01-01 00:00:00"
    assert df["timestamp"].tolist()[3] == "2020-01-01 00:10:00"  # UDI 11 = 2º passo da máquina 1
    assert df["modo_falha"].isna().tolist() == [True, False, True, True]
    assert df["modo_falha"].iloc[1] == "HDF|PWF"
    assert df["falha"].tolist() == ["0", "1", "1", "0"]
    assert AI4I_MAQUINAS_VIRTUAIS == 10


def test_bruto_particionado_por_data_e_maquina(tmp_path):
    df = quadro(
        linha(maquina_id="A", timestamp="2026-01-01 10:00:00"),
        linha(maquina_id="A", timestamp="2026-01-02 10:00:00"),
        linha(maquina_id="B", timestamp="2026-01-01 11:00:00"),
    )
    n = gravar_bruto(df, tmp_path / "bruto")
    assert n == 3
    assert (tmp_path / "bruto" / "data=2026-01-01" / "maquina_id=A").is_dir()
    assert (tmp_path / "bruto" / "data=2026-01-02" / "maquina_id=A").is_dir()
    assert (tmp_path / "bruto" / "data=2026-01-01" / "maquina_id=B").is_dir()


def test_bruto_ida_e_volta_preserva_inclusive_lixo(tmp_path):
    df = quadro(
        linha(maquina_id="A", timestamp="2026-01-01 10:00:00", torque_nm="ERRO"),
        linha(maquina_id="A", timestamp="2026-01-01 10:05:00", rotacao_rpm=None),
        linha(maquina_id=None, timestamp="2026-01-01 10:10:00"),
        linha(maquina_id="B", timestamp="ontem"),
    )
    gravar_bruto(df, tmp_path / "bruto")
    volta = ler_bruto(tmp_path / "bruto")
    chave = ["maquina_id", "timestamp"]
    esperado = df.sort_values(chave, na_position="last").reset_index(drop=True)
    obtido = volta.sort_values(chave, na_position="last").reset_index(drop=True)
    pd.testing.assert_frame_equal(esperado.astype("string"), obtido.astype("string"), check_dtype=False)


def test_gravar_bruto_e_deterministico_e_recria_a_pasta(tmp_path):
    df = quadro(linha(maquina_id="A"))
    gravar_bruto(df, tmp_path / "bruto")
    gravar_bruto(df, tmp_path / "bruto")  # segunda vez não acumula arquivos
    assert len(list((tmp_path / "bruto").rglob("*.parquet"))) == 1
