#!/usr/bin/env bash
# Inicialização do container do Airflow (chamado pelo CMD do Dockerfile).
set -euo pipefail

# Login da UI: um único usuário administrador, definido no .env
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS="${AIRFLOW_ADMIN_USER:?defina AIRFLOW_ADMIN_USER no .env}:admin"
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE="${AIRFLOW_HOME}/senhas_ui.json"

# Cria o banco "airflow" (se preciso), grava o arquivo de senhas e devolve a conexão
AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="$(python /opt/airflow-pipeline/preparar.py)"
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN

# Guarda a conexão num arquivo privado: comandos rodados depois com
# "docker compose exec airflow airflow ..." leem esse arquivo via
# AIRFLOW__DATABASE__SQL_ALCHEMY_CONN_CMD (definido no docker-compose.yml).
( umask 077 && printf '%s' "$AIRFLOW__DATABASE__SQL_ALCHEMY_CONN" > "${AIRFLOW_HOME}/conexao_db" )

echo "[airflow] aplicando migrações do banco de metadados..."
airflow db migrate

echo "[airflow] subindo em modo standalone (api-server + scheduler + dag-processor + triggerer)"
exec airflow standalone
