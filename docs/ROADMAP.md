# Roadmap do projeto

Este projeto é um portfólio de **Engenharia de Dados**.
Ele começou como um pipeline ETL simples e vai crescendo em versões.
Este documento mostra o que já está pronto e o que vem depois.

---

## Onde o projeto está

Tudo abaixo está no repositório e foi verificado (localmente e no CI).

### V1: pipeline ETL (feito)

| Item | Situação |
|---|---|
| PostgreSQL 16 rodando no Docker Compose | ✅ Feito |
| ETL em Python com Pandas | ✅ Feito |
| Camada bruta em Parquet, particionada por data e máquina | ✅ Feito |
| Limpeza com relatório de linhas descartadas | ✅ Feito |
| Carga idempotente (rodar de novo não duplica) | ✅ Feito |
| Dados carregados: **24.511 leituras** (10.000 do AI4I + 14.511 simuladas) de **18 máquinas** | ✅ Feito |
| Testes com pytest e lint com ruff | ✅ Feito |

### V2: modelagem com dbt e painel (feito)

| Item | Situação |
|---|---|
| dbt em três camadas: `staging` → `intermediate` → `marts` | ✅ Feito |
| Marts em modelo estrela: `dim_maquina`, `fct_leituras`, `fct_falhas_diarias` | ✅ Feito |
| Testes do dbt (unique, not_null, relationships, accepted_values e testes singulares) | ✅ Feito: `dbt build` com **PASS=60** (7 modelos + 53 testes) |
| Painel Streamlit que lê só os marts | ✅ Feito |
| CI no GitHub Actions com 3 jobs: `testes`, `integracao` e `dbt` | ✅ Feito |

---

## Próximas versões

A ordem abaixo é a ordem planejada. Cada versão usa o que a anterior construiu.

### V3: orquestração e qualidade

- Subir o **Airflow** localmente, no Docker.
- Criar uma DAG que roda o ETL e depois o `dbt build`.
- Enviar um **alerta** quando alguma etapa falhar.
- Adicionar testes de **freshness** (`dbt source freshness`): os dados estão atualizados?
- Adicionar testes de **volume**: chegou a quantidade esperada de linhas?
- Passar a trabalhar com **branch + Pull Request**, em vez de enviar direto para a `main`.

### V4: Databricks (Free Edition)

- Levar o Parquet de leituras para o **Databricks Free Edition**.
- Montar as camadas **bronze → silver → gold** com **PySpark**, salvando em **Delta Lake**.
- Refazer o `fct_falhas_diarias` na camada gold e comparar com o resultado do dbt.
- Estudar os cursos de fundamentos da **Databricks Academy**.

### V5: nuvem

- Guardar os dados em armazenamento de nuvem: **Azure Blob Storage / ADLS** ou **AWS S3**.
- Aprender o básico de **IAM e permissões** (quem pode ler e escrever o quê).
- Acompanhar o **custo** dos recursos.

### Depois

- **Streaming** com **Kafka**, simulando sensores enviando leituras em tempo real.

---

## Estratégia de portfólio

A ideia é ter **um repositório por tecnologia pedida no mercado de Engenharia de Dados**.
Todos usam o **mesmo domínio** (leituras de sensores e falhas de máquinas).
Assim fica fácil comparar abordagens diferentes para o mesmo problema.

**Este repositório é a base:** PostgreSQL + dbt + Airflow.

Repositórios planejados (os nomes são propostas; ainda não foram criados):

| Repositório | Versão | Foco |
|---|---|---|
| `pipeline-industrial-databricks` | V4 | PySpark + Delta Lake no Databricks |
| `pipeline-industrial-cloud` | V5 | Armazenamento, IAM e custo na nuvem |
| `pipeline-industrial-streaming` | Depois | Kafka e dados em tempo real |

Cada um deles terá um link de volta para este repositório base.

---

## Mapa de competências

Como cada área de Engenharia de Dados aparece neste projeto.

| Área | Status | Onde / quando |
|---|---|---|
| Programação | ✅ Feito | ETL em Python (Pandas, PyArrow) |
| SQL | ✅ Feito | `sql/queries.sql` (CTEs, window functions) e modelos dbt |
| Banco de dados / DW (OLTP x OLAP) | ✅ Feito | Tabelas normalizadas em `public` (OLTP) e modelo estrela nos `marts` (OLAP) |
| ETL / ELT | ✅ Feito | ETL em Python + ELT com dbt dentro do PostgreSQL |
| Orquestração | 🔜 Planejado (V3) | Airflow |
| Spark | 🔜 Planejado (V4 Databricks) | PySpark no Databricks Free Edition |
| Cloud | 🔜 Planejado (V5) | Azure Blob Storage / ADLS ou AWS S3 |
| Lake / Lakehouse | 🔜 Planejado (V4 Databricks) | Bronze/silver/gold em Delta Lake; hoje as camadas bruta → staging → marts já lembram a arquitetura medalhão |
| Streaming | 🔜 Planejado (depois) | Kafka |
| Qualidade / Observabilidade | 🟡 Em parte | Testes do dbt feitos; freshness, volume e alertas na V3 |
| Engenharia de software | ✅ Feito | Git, Docker, testes, CI e documentação |
| Projetos | ✅ Feito | Projeto completo e documentado, evoluindo por versões |

---

Este roadmap pode mudar até o fim da fase, conforme o aprendizado avança.
