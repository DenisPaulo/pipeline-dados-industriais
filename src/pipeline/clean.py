"""Limpeza: tipos, duplicados, nulos e faixas físicas, com relatório de linhas descartadas.

Cada linha descartada recebe exatamente UM motivo (o primeiro que se aplica, na ordem de
``MOTIVOS``), o que permite conferir: linhas de entrada = linhas válidas + linhas descartadas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .schemas import (
    FAIXAS_FISICAS,
    MODO_DESCONHECIDO,
    MODOS_FALHA,
    SENSORES,
    TIPOS_PRODUTO,
)

CHAVE = ["fonte", "maquina_id", "timestamp"]
COLUNAS_INTEIRAS = ["rotacao_rpm", "desgaste_min"]

# Ordem de prioridade dos motivos de descarte
MOTIVOS = [
    "duplicada",
    "maquina_ausente",
    "timestamp_invalido",
    "tipo_invalido",
    "falha_invalida",
    "sensor_nulo",
    "sensor_nao_numerico",
    "fora_da_faixa_fisica",
]


def _vazio(serie: pd.Series) -> pd.Series:
    return serie.isna() | (serie.astype("string").str.strip() == "")


def limpar(bruto: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """Limpa a camada bruta.

    Retorna ``(leituras, falhas, descartadas, relatorio)``:

    - ``leituras``: uma linha por (máquina, instante), com tipos corretos;
    - ``falhas``: uma linha por (máquina, instante, modo) das leituras com falha;
    - ``descartadas``: linhas rejeitadas, com a coluna ``motivo``;
    - ``relatorio``: contagens para auditoria.
    """
    df = bruto.reset_index(drop=True).copy()
    n_entrada = len(df)
    for col in df.columns:
        df[col] = df[col].astype("string").str.strip()

    # --- diagnósticos por linha (cada máscara é independente) -----------------------------
    ts = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    num = {c: pd.to_numeric(df[c], errors="coerce") for c in SENSORES}
    masc: dict[str, pd.Series] = {
        "duplicada": df.duplicated(subset=CHAVE, keep="first") & ~_vazio(df["maquina_id"]) & ts.notna(),
        "maquina_ausente": _vazio(df["maquina_id"]),
        "timestamp_invalido": ts.isna(),
        "tipo_invalido": ~df["tipo"].isin(TIPOS_PRODUTO),
        "falha_invalida": ~df["falha"].isin(["0", "1"]),
        "sensor_nulo": pd.concat([_vazio(df[c]) for c in SENSORES], axis=1).any(axis=1),
        "sensor_nao_numerico": pd.concat([num[c].isna() & ~_vazio(df[c]) for c in SENSORES], axis=1).any(
            axis=1
        ),
        "fora_da_faixa_fisica": pd.concat(
            [(num[c] < FAIXAS_FISICAS[c][0]) | (num[c] > FAIXAS_FISICAS[c][1]) for c in SENSORES],
            axis=1,
        ).any(axis=1),
    }

    # --- um motivo por linha, pela ordem de prioridade -------------------------------------
    motivo = pd.Series(pd.NA, index=df.index, dtype="string")
    for nome in MOTIVOS:
        motivo = motivo.mask(motivo.isna() & masc[nome], nome)
    descartar = motivo.notna()

    descartadas = bruto.reset_index(drop=True).loc[descartar].copy()
    descartadas["motivo"] = motivo[descartar].to_numpy()

    # --- tipos corretos nas linhas válidas -----------------------------------------------
    ok = df.loc[~descartar]
    leituras = pd.DataFrame(
        {
            "fonte": ok["fonte"].astype(str),
            "maquina_id": ok["maquina_id"].astype(str),
            "ts": ts[~descartar],
            "tipo_produto": ok["tipo"].astype(str),
            **{c: num[c][~descartar].astype("float64") for c in SENSORES},
            "falha": ok["falha"].astype(int).astype(bool),
        }
    )
    for c in COLUNAS_INTEIRAS:
        leituras[c] = leituras[c].round().astype("int64")
    leituras = leituras.sort_values(["maquina_id", "ts"]).reset_index(drop=True)

    # --- falhas: um registro por modo; falha sem modo informado vira DESCONHECIDO ----------
    modos = ok["modo_falha"].fillna("")
    avisos = {"modo_ignorado_sem_falha": int(((modos != "") & (ok["falha"] == "0")).sum())}
    base = pd.DataFrame(
        {
            "maquina_id": ok["maquina_id"].astype(str),
            "ts": ts[~descartar],
            "modo": modos.str.split("|"),
            "falha": ok["falha"] == "1",
        }
    )
    base = base[base["falha"]].drop(columns="falha")
    base["modo"] = base["modo"].map(lambda ms: [m for m in ms if m in MODOS_FALHA] or [MODO_DESCONHECIDO])
    falhas = (
        base.explode("modo")
        .drop_duplicates()
        .sort_values(["maquina_id", "ts", "modo"])
        .reset_index(drop=True)
    )
    avisos["falhas_sem_modo_informado"] = int((falhas["modo"] == MODO_DESCONHECIDO).sum())

    por_motivo = {m: int((motivo == m).sum()) for m in MOTIVOS}
    relatorio = {
        "linhas_entrada": n_entrada,
        "linhas_validas": len(leituras),
        "linhas_descartadas": int(descartar.sum()),
        "descartadas_por_motivo": por_motivo,
        "avisos": avisos,
        "por_fonte": {
            f: {
                "entrada": int((df["fonte"] == f).sum()),
                "validas": int((leituras["fonte"] == f).sum()),
            }
            for f in sorted(df["fonte"].dropna().unique())
        },
        "leituras_com_falha": int(leituras["falha"].sum()),
        "registros_de_falha": len(falhas),
    }
    assert relatorio["linhas_validas"] + relatorio["linhas_descartadas"] == n_entrada
    return leituras, falhas, descartadas, relatorio


def gravar_limpo(
    leituras: pd.DataFrame,
    falhas: pd.DataFrame,
    descartadas: pd.DataFrame,
    relatorio: dict,
    limpo_dir: Path,
    relatorio_path: Path,
) -> None:
    limpo_dir.mkdir(parents=True, exist_ok=True)
    leituras.to_parquet(limpo_dir / "leituras.parquet", index=False)
    falhas.to_parquet(limpo_dir / "falhas.parquet", index=False)
    descartadas.to_parquet(limpo_dir / "descartadas.parquet", index=False)
    relatorio_path.parent.mkdir(parents=True, exist_ok=True)
    relatorio_path.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False), encoding="utf-8")


def ler_limpo(limpo_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        pd.read_parquet(limpo_dir / "leituras.parquet"),
        pd.read_parquet(limpo_dir / "falhas.parquet"),
    )


def formatar_relatorio(rel: dict) -> str:
    linhas = [
        "[limpeza] relatório de linhas",
        f"  entrada:     {rel['linhas_entrada']:>8}",
        f"  válidas:     {rel['linhas_validas']:>8}",
        f"  descartadas: {rel['linhas_descartadas']:>8}",
    ]
    for motivo, n in rel["descartadas_por_motivo"].items():
        if n:
            linhas.append(f"    - {motivo}: {n}")
    for aviso, n in rel["avisos"].items():
        if n:
            linhas.append(f"  aviso {aviso}: {n}")
    for fonte, c in rel["por_fonte"].items():
        linhas.append(f"  fonte {fonte}: {c['entrada']} -> {c['validas']}")
    return "\n".join(linhas)
