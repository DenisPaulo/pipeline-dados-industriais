# Airflow (V3) para orquestrar o pipeline: ETL Python -> dbt build.
# Contexto de build = raiz do repositório (para copiar os requirements do ETL e do dbt).
FROM apache/airflow:3.3.2-python3.12

# O ETL e o dbt ficam em ambientes virtuais SEPARADOS do Airflow:
# assim as versões do projeto (pandas, dbt...) não brigam com as dependências do próprio Airflow.
COPY requirements.txt /tmp/req-etl.txt
COPY dbt/requirements.txt /tmp/req-dbt.txt
RUN python -m venv /home/airflow/venvs/etl \
    && /home/airflow/venvs/etl/bin/pip install --no-cache-dir -r /tmp/req-etl.txt \
    && python -m venv /home/airflow/venvs/dbt \
    && /home/airflow/venvs/dbt/bin/pip install --no-cache-dir -r /tmp/req-dbt.txt

# Pasta de dados do ETL (vira um volume nomeado; precisa existir com dono "airflow")
USER root
RUN mkdir -p /opt/pipeline/data && chown -R airflow:0 /opt/pipeline/data && chmod -R g+rwX /opt/pipeline/data

# Script de inicialização. O sed remove CRLF caso o arquivo venha de um checkout no Windows.
COPY airflow/preparar.py airflow/iniciar.sh /opt/airflow-pipeline/
RUN sed -i 's/\r$//' /opt/airflow-pipeline/iniciar.sh /opt/airflow-pipeline/preparar.py \
    && chmod 755 /opt/airflow-pipeline && chmod 644 /opt/airflow-pipeline/*
USER airflow

CMD ["bash", "/opt/airflow-pipeline/iniciar.sh"]
