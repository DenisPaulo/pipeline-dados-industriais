"""Contrato de colunas e faixas físicas compartilhado entre as etapas."""

from __future__ import annotations

SENSORES = ["temp_ar_k", "temp_processo_k", "rotacao_rpm", "torque_nm", "desgaste_min"]

# Camada bruta: tudo texto, exatamente como veio da fonte (sem perda).
COLUNAS_BRUTO = [
    "fonte",
    "maquina_id",
    "timestamp",
    "tipo",
    *SENSORES,
    "falha",
    "modo_falha",
]

MODOS_FALHA = ["TWF", "HDF", "PWF", "OSF", "RNF"]
MODO_DESCONHECIDO = "DESCONHECIDO"
TIPOS_PRODUTO = ["L", "M", "H"]

# Faixas fisicamente plausíveis (largas de propósito: pegam erro de unidade/sensor, não variação normal).
FAIXAS_FISICAS: dict[str, tuple[float, float]] = {
    "temp_ar_k": (250.0, 350.0),
    "temp_processo_k": (250.0, 400.0),
    "rotacao_rpm": (0.0, 10_000.0),
    "torque_nm": (0.0, 200.0),
    "desgaste_min": (0.0, 1_000.0),
}

PARTICAO_SEM_DATA = "sem_data"
PARTICAO_SEM_MAQUINA = "sem_maquina"
