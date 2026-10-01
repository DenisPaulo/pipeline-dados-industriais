import pandas as pd

from pipeline.clean import MOTIVOS, limpar
from tests.conftest import linha, quadro


def test_contagem_e_motivos(bruto_misto):
    leituras, falhas, descartadas, rel = limpar(bruto_misto)
    assert rel["linhas_entrada"] == 12
    assert rel["linhas_validas"] == 3 == len(leituras)
    assert rel["linhas_descartadas"] == 9 == len(descartadas)
    assert rel["linhas_validas"] + rel["linhas_descartadas"] == rel["linhas_entrada"]
    assert rel["descartadas_por_motivo"] == {
        "duplicada": 1,
        "maquina_ausente": 1,
        "timestamp_invalido": 1,
        "tipo_invalido": 1,
        "falha_invalida": 1,
        "sensor_nulo": 1,
        "sensor_nao_numerico": 1,
        "fora_da_faixa_fisica": 2,
    }
    assert set(descartadas["motivo"]) <= set(MOTIVOS)


def test_cada_linha_descartada_tem_um_motivo(bruto_misto):
    _, _, descartadas, _ = limpar(bruto_misto)
    assert descartadas["motivo"].notna().all()
    assert len(descartadas) == len(descartadas.drop_duplicates(subset=["timestamp", "maquina_id", "motivo"]))


def test_tipos_das_leituras(bruto_misto):
    leituras, _, _, _ = limpar(bruto_misto)
    assert str(leituras["ts"].dtype).startswith("datetime64")
    assert leituras["rotacao_rpm"].dtype == "int64"
    assert leituras["desgaste_min"].dtype == "int64"
    assert leituras["temp_ar_k"].dtype == "float64"
    assert leituras["falha"].dtype == bool
    assert leituras["falha"].tolist() == [False, True, False]


def test_falhas_um_registro_por_modo(bruto_misto):
    _, falhas, _, rel = limpar(bruto_misto)
    assert falhas["modo"].tolist() == ["HDF", "PWF"]
    assert rel["registros_de_falha"] == 2


def test_falha_sem_modo_vira_desconhecido():
    _, falhas, _, rel = limpar(quadro(linha(falha="1", modo_falha=None)))
    assert falhas["modo"].tolist() == ["DESCONHECIDO"]
    assert rel["avisos"]["falhas_sem_modo_informado"] == 1


def test_modo_sem_falha_e_ignorado_e_avisado():
    _, falhas, _, rel = limpar(quadro(linha(falha="0", modo_falha="TWF")))
    assert falhas.empty
    assert rel["avisos"]["modo_ignorado_sem_falha"] == 1


def test_duplicata_mantem_a_primeira_ocorrencia():
    a = linha(torque_nm="40.0")
    b = linha(torque_nm="41.0")  # mesma chave (fonte, máquina, instante)
    leituras, _, descartadas, _ = limpar(quadro(a, b))
    assert leituras["torque_nm"].tolist() == [40.0]
    assert descartadas["motivo"].tolist() == ["duplicada"]


def test_mesma_chave_em_fontes_diferentes_nao_e_duplicata():
    leituras, _, _, rel = limpar(quadro(linha(fonte="a", maquina_id="X"), linha(fonte="b", maquina_id="Y")))
    assert len(leituras) == 2 and rel["linhas_descartadas"] == 0


def test_limites_da_faixa_sao_inclusivos():
    ok = linha(temp_ar_k="250.0", rotacao_rpm="0", torque_nm="200.0")
    fora = linha(timestamp="2026-01-01 00:05:00", rotacao_rpm="10001")
    leituras, _, descartadas, _ = limpar(quadro(ok, fora))
    assert len(leituras) == 1
    assert descartadas["motivo"].tolist() == ["fora_da_faixa_fisica"]


def test_espacos_em_branco_contam_como_nulo():
    _, _, descartadas, _ = limpar(quadro(linha(torque_nm="   ")))
    assert descartadas["motivo"].tolist() == ["sensor_nulo"]


def test_entrada_vazia():
    leituras, falhas, descartadas, rel = limpar(quadro())
    assert len(leituras) == len(falhas) == len(descartadas) == 0
    assert rel["linhas_entrada"] == 0


def test_nao_altera_o_dataframe_de_entrada(bruto_misto):
    copia = bruto_misto.copy(deep=True)
    limpar(bruto_misto)
    pd.testing.assert_frame_equal(bruto_misto, copia)
