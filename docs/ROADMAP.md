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

### V4: nuvem (Azure)

- Guardar os arquivos Parquet no **Azure Blob Storage / ADLS**.
- Organizar em camadas **bronze / silver / gold**.
- Aprender o básico de **IAM e permissões** (quem pode ler e escrever o quê).
- Acompanhar o **custo** dos recursos.

### V5: Spark e Lakehouse

- Reescrever uma etapa do ETL em **PySpark**.
- Salvar o resultado em **Delta Lake**, com particionamento.

### Depois

- **Streaming** com **Kafka**, simulando sensores industriais enviando dados em tempo real.

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
| Spark | 🔜 Planejado (V5) | PySpark |
| Cloud | 🔜 Planejado (V4) | Azure Blob Storage / ADLS |
| Lake / Lakehouse | 🟡 Em parte | As camadas bruta → staging → marts lembram a arquitetura medalhão; Delta Lake na V5 |
| Streaming | 🔜 Planejado (depois) | Kafka |
| Qualidade / Observabilidade | 🟡 Em parte | Testes do dbt feitos; freshness, volume e alertas na V3 |
| Engenharia de software | ✅ Feito | Git, Docker, testes, CI e documentação |
| Projetos | ✅ Feito | Projeto completo e documentado, evoluindo por versões |

---

Este roadmap pode mudar até o fim da fase, conforme o aprendizado avança.
