"""Preparação do Airflow antes de subir (roda a cada start; é idempotente).

1. Cria o banco `airflow` no PostgreSQL do compose, se ainda não existir
   (o banco de metadados do Airflow fica separado dos dados do pipeline).
2. Grava o arquivo de senhas do login da UI a partir de AIRFLOW_ADMIN_USER/PASSWORD.
3. Imprime a string de conexão (com a senha codificada para URL) para o iniciar.sh.
"""

from __future__ import annotations

import json
import os
import sys
import time
from urllib.parse import quote

import psycopg2
from psycopg2 import sql

BANCO_AIRFLOW = os.environ.get("AIRFLOW_DB", "airflow")


def obrigatoria(nome: str) -> str:
    valor = os.environ.get(nome)
    if not valor:
        sys.exit(f"[airflow] variável {nome} não definida. Confira o arquivo .env (veja .env.example).")
    return valor


def main() -> None:
    usuario = os.environ.get("POSTGRES_USER", "pipeline")
    senha = obrigatoria("POSTGRES_PASSWORD")
    host = os.environ.get("POSTGRES_HOST", "postgres")
    porta = os.environ.get("POSTGRES_PORT", "5432")
    banco_dados = os.environ.get("POSTGRES_DB", "pipeline")
    admin_user = obrigatoria("AIRFLOW_ADMIN_USER")
    admin_senha = obrigatoria("AIRFLOW_ADMIN_PASSWORD")

    for tentativa in range(1, 31):
        try:
            conn = psycopg2.connect(dbname=banco_dados, user=usuario, password=senha, host=host, port=porta)
            break
        except psycopg2.OperationalError as exc:
            print(f"[airflow] esperando o PostgreSQL ({tentativa}/30): {exc}".strip(), file=sys.stderr)
            time.sleep(2)
    else:
        sys.exit("[airflow] PostgreSQL indisponível.")

    conn.autocommit = True  # CREATE DATABASE não roda dentro de transação
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (BANCO_AIRFLOW,))
        if cur.fetchone() is None:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(BANCO_AIRFLOW)))
            print(f"[airflow] banco '{BANCO_AIRFLOW}' criado.", file=sys.stderr)
        else:
            print(f"[airflow] banco '{BANCO_AIRFLOW}' já existe.", file=sys.stderr)
    conn.close()

    arquivo_senhas = os.environ["AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE"]
    with open(arquivo_senhas, "w", encoding="utf-8") as f:
        json.dump({admin_user: admin_senha}, f)
    os.chmod(arquivo_senhas, 0o600)

    credenciais = f"{quote(usuario, safe='')}:{quote(senha, safe='')}"
    print(f"postgresql+psycopg2://{credenciais}@{host}:{porta}/{BANCO_AIRFLOW}")


if __name__ == "__main__":
    main()
