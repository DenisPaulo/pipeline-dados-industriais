"""Orquestra o pipeline de ponta a ponta.

python -m pipeline.run                # ingestão -> limpeza -> carga
python -m pipeline.run --sem-carga    # só ingestão e limpeza (não precisa de PostgreSQL)
"""

from __future__ import annotations

import argparse
import json
import time

from . import clean, ingest, load
from .config import Config


def executar(cfg: Config, com_carga: bool = True) -> dict:
    t0 = time.perf_counter()
    resumo: dict = {}

    t = time.perf_counter()
    bruto = ingest.ingerir(cfg)
    resumo["ingestao"] = {"linhas": len(bruto), "segundos": round(time.perf_counter() - t, 2)}

    t = time.perf_counter()
    bruto = ingest.ler_bruto(cfg.bruto_dir)  # a limpeza parte da camada bruta gravada em disco
    leituras, falhas, descartadas, rel = clean.limpar(bruto)
    clean.gravar_limpo(leituras, falhas, descartadas, rel, cfg.limpo_dir, cfg.relatorio_path)
    print(clean.formatar_relatorio(rel))
    resumo["limpeza"] = {
        "entrada": rel["linhas_entrada"],
        "validas": rel["linhas_validas"],
        "descartadas": rel["linhas_descartadas"],
        "segundos": round(time.perf_counter() - t, 2),
    }

    if com_carga:
        t = time.perf_counter()
        conn = load.conectar(cfg)
        try:
            load.aplicar_schema(conn, cfg.sql_dir / "schema.sql")
            mudancas = load.carregar(conn, leituras, falhas)
            totais = load.contagens(conn)
        finally:
            conn.close()
        print(f"[carga] {mudancas}")
        print(f"[carga] totais no banco: {totais}")
        resumo["carga"] = {
            **mudancas,
            "totais": totais,
            "segundos": round(time.perf_counter() - t, 2),
        }

    resumo["segundos_total"] = round(time.perf_counter() - t0, 2)
    print("[resumo] " + json.dumps(resumo, ensure_ascii=False))
    return resumo


def main() -> None:
    p = argparse.ArgumentParser(description="Pipeline ETL de sensores industriais")
    p.add_argument("--sem-carga", action="store_true", help="não carrega no PostgreSQL")
    args = p.parse_args()
    executar(Config.do_ambiente(), com_carga=not args.sem_carga)


if __name__ == "__main__":
    main()
