# dbt (V2): transformações dentro do PostgreSQL

O pipeline Python (V1) carrega as tabelas `maquinas`, `leituras` e `falhas` no PostgreSQL. O **dbt** (*data build tool*) pega essas tabelas e cria **novas visões e tabelas usando só SQL**, com testes automáticos de qualidade. Esta primeira etapa traz a **camada staging**: nomes de colunas claros e temperaturas também em Celsius.

> Projeto educacional. Por enquanto só existe a camada `staging` (3 views). As camadas seguintes (regras de negócio, métricas) virão nas próximas etapas da V2.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `dbt_project.yml` | Configuração do projeto: nome, pastas e como cada camada é materializada (`staging` = *view*, no schema `staging`). |
| `profiles.yml` | Como o dbt conecta no banco. **Sem senha no arquivo**: usa as variáveis `POSTGRES_*` (as mesmas do `.env`). Só `POSTGRES_PASSWORD` é obrigatória. |
| `requirements.txt` | Versões fixas: `dbt-core 1.12.5` e `dbt-postgres 1.11.0`. |
| `Dockerfile` | Imagem Python com o dbt instalado (usada pelo serviço `dbt` do `docker-compose.yml`). |
| `macros/generate_schema_name.sql` | Faz o schema ser exatamente `staging` (e não `analytics_staging`, que é o comportamento padrão do dbt). |
| `models/staging/_sources.yml` | Declara as *sources*: tabelas que o dbt não cria (`maquinas`, `leituras`, `falhas`), com descrição das colunas. |
| `models/staging/stg_maquinas.sql` | View de máquinas (`maquina_id` → `id_maquina`). |
| `models/staging/stg_leituras.sql` | View de leituras: nomes claros (`ts` → `medido_em`, `falha` → `houve_falha`) e temperaturas em Celsius (`temperatura_ar_c`, `temperatura_processo_c` = Kelvin − 273,15). |
| `models/staging/stg_falhas.sql` | View de falhas (`modo` → `modo_falha`). |
| `models/staging/_staging.yml` | Descrições dos modelos e **25 testes**: `unique`, `not_null`, `relationships` (chaves estrangeiras) e `accepted_values` (`fonte`, `tipo_produto` e `modo_falha`). |

Os arquivos que começam com `_` são só configuração (YAML); os `.sql` são os modelos.

## Como rodar (Docker)

Pré-requisitos: `.env` criado (veja o README principal) e os dados já carregados pelo pipeline Python.

```bash
docker compose up -d --wait postgres        # sobe o banco (ou: make up)
docker compose run --rm app                 # carrega os dados (ou: make run)

docker compose run --rm --build dbt debug   # testa a conexão   (ou: make dbt-debug)
docker compose run --rm --build dbt build   # cria views + roda testes   (ou: make dbt-build)
```

O serviço `dbt` tem o *profile* `dbt`, então **não sobe** com um `docker compose up` comum e não afeta o fluxo da V1. A pasta `dbt/` é montada somente leitura dentro do container.

Depois, no banco:

```sql
SELECT id_maquina, medido_em, temperatura_ar_k, temperatura_ar_c FROM staging.stg_leituras LIMIT 5;
```

## Como rodar sem Docker

```bash
pip install -r dbt/requirements.txt
export POSTGRES_PASSWORD=...   # e POSTGRES_HOST/PORT/USER/DB se não forem os padrões
cd dbt
dbt debug --profiles-dir .
dbt build --profiles-dir .
```

## Resultado esperado

`dbt build` cria 3 views e executa 25 testes: `Done. PASS=28 WARN=0 ERROR=0 SKIP=0 TOTAL=28`.
Se um teste falhar, o dbt mostra qual e quantas linhas violaram a regra.
