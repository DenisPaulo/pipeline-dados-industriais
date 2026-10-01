import pytest

from pipeline.config import Config, ErroConfiguracao


def test_padroes_sem_senha():
    cfg = Config.do_ambiente({})
    assert cfg.fontes == ("ai4i", "simulado") and cfg.semente == 42 and cfg.db_porta == 5432
    with pytest.raises(ErroConfiguracao, match="POSTGRES_PASSWORD"):
        cfg.conexao_kwargs()


def test_le_do_ambiente():
    cfg = Config.do_ambiente(
        {
            "POSTGRES_PASSWORD": "x",
            "POSTGRES_HOST": "banco",
            "POSTGRES_PORT": "5544",
            "PIPELINE_FONTES": "simulado",
            "PIPELINE_SEMENTE": "7",
        }
    )
    assert cfg.conexao_kwargs()["host"] == "banco" and cfg.conexao_kwargs()["port"] == 5544
    assert cfg.fontes == ("simulado",) and cfg.semente == 7


@pytest.mark.parametrize(
    "env", [{"PIPELINE_FONTES": "csv"}, {"PIPELINE_FONTES": ""}, {"POSTGRES_PORT": "abc"}]
)
def test_valores_invalidos(env):
    with pytest.raises(ErroConfiguracao):
        Config.do_ambiente(env)
