"""Ingestão: obtém as fontes e grava a camada bruta em Parquet (particionada por data/máquina).

A camada bruta guarda tudo como texto, sem corrigir nada: a limpeza vem depois e fica auditável.
"""

from __future__ import annotations

import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.dataset as ds
import pyarrow.parquet as pq

from .config import Config
from .schemas import (
    COLUNAS_BRUTO,
    MODOS_FALHA,
    PARTICAO_SEM_DATA,
    PARTICAO_SEM_MAQUINA,
)
from .simulador import gerar_leituras, gravar_csv

# Mesmo endereço oficial usado no projeto manutencao-preditiva-ia
DATASET_URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
CSV_AI4I = "ai4i2020.csv"
CSV_SIMULADO = "leituras_simuladas.csv"

# O AI4I não traz máquina nem horário. Para exercitar o modelo relacional, cada registro (UDI)
# é atribuído a uma de N "máquinas virtuais" em rodízio, com uma leitura a cada 10 minutos.
# Isto é uma decisão didática do pipeline: não tem significado físico.
AI4I_MAQUINAS_VIRTUAIS = 10
AI4I_INICIO = pd.Timestamp("2020-01-01 00:00:00")
AI4I_INTERVALO_MIN = 10

_PARTICOES = ["data", "maquina_id"]
_SCHEMA_PARTICAO = pa.schema([("data", pa.string()), ("maquina_id", pa.string())])


def baixar_ai4i(destino_dir: Path, forcar: bool = False, timeout: int = 60) -> Path:
    """Baixa o .zip oficial do UCI e extrai o CSV em ``destino_dir`` (idempotente)."""
    csv_path = destino_dir / CSV_AI4I
    if csv_path.exists() and not forcar:
        print(f"[ingestão] {csv_path.name} já existe — download ignorado.")
        return csv_path
    destino_dir.mkdir(parents=True, exist_ok=True)
    print(f"[ingestão] baixando {DATASET_URL}")
    req = urllib.request.Request(DATASET_URL, headers={"User-Agent": "pipeline-dados-industriais"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (URL fixa, https)
        carga = resp.read()
    with zipfile.ZipFile(io.BytesIO(carga)) as zf:
        if CSV_AI4I not in zf.namelist():
            raise FileNotFoundError(f"'{CSV_AI4I}' não está no zip: {zf.namelist()}")
        tmp = csv_path.with_suffix(".csv.tmp")
        tmp.write_bytes(zf.read(CSV_AI4I))
        tmp.replace(csv_path)
    return csv_path


def ler_ai4i(csv_path: Path) -> pd.DataFrame:
    """Lê o CSV do AI4I e converte para o esquema bruto (tudo texto)."""
    cru = pd.read_csv(csv_path, dtype=str)
    udi = pd.to_numeric(cru["UDI"], errors="raise").astype(int)
    passo = (udi - 1) // AI4I_MAQUINAS_VIRTUAIS
    ts = AI4I_INICIO + pd.to_timedelta(passo * AI4I_INTERVALO_MIN, unit="min")
    maq = (udi - 1) % AI4I_MAQUINAS_VIRTUAIS + 1

    def modos(linha: pd.Series) -> str | None:
        ativos = [m for m in MODOS_FALHA if linha.get(m) == "1"]
        return "|".join(ativos) or None

    df = pd.DataFrame(
        {
            "fonte": "ai4i",
            "maquina_id": "AI4I-" + maq.astype(str).str.zfill(2),
            "timestamp": ts.dt.strftime("%Y-%m-%d %H:%M:%S"),
            "tipo": cru["Type"],
            "temp_ar_k": cru["Air temperature [K]"],
            "temp_processo_k": cru["Process temperature [K]"],
            "rotacao_rpm": cru["Rotational speed [rpm]"],
            "torque_nm": cru["Torque [Nm]"],
            "desgaste_min": cru["Tool wear [min]"],
            "falha": cru["Machine failure"],
            "modo_falha": cru[MODOS_FALHA].apply(modos, axis=1),
        }
    )
    return df[COLUNAS_BRUTO]


def obter_simulado(raw_dir: Path, semente: int) -> pd.DataFrame:
    """Gera (semente fixa) o CSV simulado em ``raw_dir`` e o lê de volta como bruto."""
    df, resumo = gerar_leituras(semente=semente)
    caminho = gravar_csv(df, raw_dir / "simulado" / CSV_SIMULADO)
    print(f"[ingestão] simulado: {caminho.name} gerado com semente {semente} — injetado: {resumo}")
    return pd.read_csv(caminho, dtype=str)[COLUNAS_BRUTO]


def gravar_bruto(df: pd.DataFrame, bruto_dir: Path) -> int:
    """Grava a camada bruta em Parquet particionado por ``data=AAAA-MM-DD/maquina_id=...``.

    Recria a pasta inteira a cada execução (determinístico). Retorna o nº de partições.
    """
    if bruto_dir.exists():
        shutil.rmtree(bruto_dir)
    bruto_dir.mkdir(parents=True)
    out = df.copy()
    out["data"] = out["timestamp"].str.slice(0, 10).fillna(PARTICAO_SEM_DATA)
    out.loc[out["data"].str.len() != 10, "data"] = PARTICAO_SEM_DATA
    out["maquina_id"] = out["maquina_id"].fillna(PARTICAO_SEM_MAQUINA)
    tabela = pa.Table.from_pandas(out.astype(object).where(out.notna(), None), preserve_index=False)
    pq.write_to_dataset(
        tabela,
        root_path=str(bruto_dir),
        partition_cols=_PARTICOES,
        basename_template="parte-{i}.parquet",
        existing_data_behavior="delete_matching",
    )
    return sum(1 for _ in bruto_dir.glob("data=*/maquina_id=*"))


def ler_bruto(bruto_dir: Path) -> pd.DataFrame:
    """Lê a camada bruta (todas as partições) de volta com o esquema bruto."""
    dataset = ds.dataset(
        bruto_dir,
        format="parquet",
        partitioning=ds.partitioning(_SCHEMA_PARTICAO, flavor="hive"),
    )
    df = dataset.to_table().to_pandas()
    df["maquina_id"] = df["maquina_id"].astype(object).where(df["maquina_id"] != PARTICAO_SEM_MAQUINA, None)
    return df[COLUNAS_BRUTO].reset_index(drop=True)


def ingerir(cfg: Config) -> pd.DataFrame:
    """Executa a ingestão das fontes configuradas e grava a camada bruta."""
    partes = []
    if "ai4i" in cfg.fontes:
        csv = baixar_ai4i(cfg.raw_dir / "ai4i")
        partes.append(ler_ai4i(csv))
    if "simulado" in cfg.fontes:
        partes.append(obter_simulado(cfg.raw_dir, cfg.semente))
    df = pd.concat(partes, ignore_index=True)
    n_particoes = gravar_bruto(df, cfg.bruto_dir)
    print(f"[ingestão] {len(df)} linhas -> {n_particoes} partições em {cfg.bruto_dir}")
    return df
