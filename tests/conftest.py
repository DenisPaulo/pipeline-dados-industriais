"""Dados sintéticos pequenos, escritos à mão, para testes rápidos e determinísticos."""

from __future__ import annotations

import pandas as pd
import pytest

from pipeline.schemas import COLUNAS_BRUTO


def linha(**kw) -> dict:
    base = {
        "fonte": "simulado",
        "maquina_id": "M-01",
        "timestamp": "2026-01-01 00:00:00",
        "tipo": "L",
        "temp_ar_k": "300.0",
        "temp_processo_k": "310.0",
        "rotacao_rpm": "1500",
        "torque_nm": "40.0",
        "desgaste_min": "10",
        "falha": "0",
        "modo_falha": None,
    }
    base.update(kw)
    return base


def quadro(*linhas: dict) -> pd.DataFrame:
    return pd.DataFrame(list(linhas), columns=COLUNAS_BRUTO).astype("object")


@pytest.fixture
def bruto_misto() -> pd.DataFrame:
    """12 linhas: 3 válidas (1 com falha) e 9 com um problema cada (1 duplicada)."""
    return quadro(
        linha(timestamp="2026-01-01 00:00:00"),  # válida
        linha(timestamp="2026-01-01 00:05:00", falha="1", modo_falha="HDF|PWF"),  # válida, 2 modos
        linha(timestamp="2026-01-01 00:10:00"),  # válida
        linha(timestamp="2026-01-01 00:10:00"),  # duplicada da anterior
        linha(timestamp="2026-01-01 00:15:00", torque_nm=None),  # sensor nulo
        linha(timestamp="2026-01-01 00:20:00", rotacao_rpm="ERRO"),  # não numérico
        linha(timestamp="2026-01-01 00:25:00", temp_ar_k="25.0"),  # °C no lugar de K
        linha(timestamp="2026-01-01 00:30:00", torque_nm="-5.0"),  # negativo
        linha(timestamp="ontem"),  # timestamp inválido
        linha(maquina_id=None, timestamp="2026-01-01 00:35:00"),  # sem máquina
        linha(timestamp="2026-01-01 00:40:00", tipo="X"),  # tipo inválido
        linha(timestamp="2026-01-01 00:45:00", falha="talvez"),  # falha inválida
    )
