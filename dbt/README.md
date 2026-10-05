# dbt (V2): transformações dentro do PostgreSQL

O pipeline Python (V1) carrega as tabelas `maquinas`, `leituras` e `falhas` no PostgreSQL. O **dbt** (*data build tool*) pega essas tabelas e cria **novas visões e tabelas usando só SQL**, com testes automáticos de qualidade. Hoje o projeto tem três camadas: **staging** (nomes de colunas claros e temperaturas também em Celsius), **intermediate** (leituras enriquecidas) e **marts** (tabelas finais: `dim_maquina` e `fct_leituras`).

> Projeto educacional. Outras dimensões/fatos e o painel virão nas próximas etapas da V2.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `dbt_project.yml` | Configuração do projeto: nome, pastas e materialização: `staging` e `intermediate` = *view*; `marts` = *table* (schemas `staging`, `intermediate` e `marts`). |
| `profiles.yml` | Como o dbt conecta no banco. **Sem senha no arquivo**: usa as variáveis `POSTGRES_*` (as mesmas do `.env`). Só `POSTGRES_PASSWORD` é obrigatória. |
| `requirements.txt` | Versões fixas: `dbt-core 1.12.5` e `dbt-postgres 1.11.0`. |
| `Dockerfile` | Imagem Python com o dbt instalado (usada pelo serviço `dbt` do `docker-compose.yml`). |
| `macros/generate_schema_name.sql` | Faz o schema ser exatamente o definido na camada (`staging`, `intermediate`, `marts`) e não `analytics_staging`, que é o comportamento padrão do dbt. |
| `models/staging/_sources.yml` | Declara as *sources*: tabelas que o dbt não cria (`maquinas`, `leituras`, `falhas`), com descrição das colunas. |
| `models/staging/stg_maquinas.sql` | View de máquinas (`maquina_id` → `id_maquina`). |
| `models/staging/stg_leituras.sql` | View de leituras: nomes claros (`ts` → `medido_em`, `falha` → `houve_falha`) e temperaturas em Celsius (`temperatura_ar_c`, `temperatura_processo_c` = Kelvin − 273,15). |
| `models/staging/stg_falhas.sql` | View de falhas (`modo` → `modo_falha`). |
| `models/staging/_staging.yml` | Descrições dos modelos e **25 testes**: `unique`, `not_null`, `relationships` (chaves estrangeiras) e `accepted_values` (`fonte`, `tipo_produto` e `modo_falha`). |

| `models/intermediate/int_leituras_enriquecidas.sql` | Uma linha por leitura, com a `fonte` da máquina, os modos de falha agregados (`modos_falha`, `qtd_modos_falha`) e as medições dos sensores. A agregação em CTE evita duplicar as leituras que têm mais de um modo de falha. |
| `models/intermediate/_intermediate.yml` | Descrições e 6 testes do modelo: `unique` e `not_null` em `id_leitura`, `not_null` e `relationships` (com `stg_maquinas`) em `id_maquina`, `not_null` e `accepted_values` em `fonte`. |
| `tests/int_leituras_enriquecidas_sem_duplicacao.sql` | Teste singular (um SELECT que deve devolver 0 linhas): a contagem do intermediate tem que ser igual à do `stg_leituras`. |
| `models/marts/dim_maquina.sql` | Dimensão de máquina: uma linha por máquina, com `fonte`, `criada_em` e totais de leituras e falhas. Materializada como **tabela** no schema `marts`. |
| `models/marts/_marts.yml` | Descrições e testes de `dim_maquina` e `fct_leituras` (unique, not_null, relationships, accepted_values). |
| `tests/dim_maquina_sem_perda.sql` | Teste singular: a contagem de `dim_maquina` tem que ser igual à de `stg_maquinas`. |
| `models/marts/fct_leituras.sql` | Fato de leituras: uma linha por leitura (medidas + falha), apontando para `dim_maquina`. Tabela no schema `marts`. |
| `tests/fct_leituras_sem_perda.sql` | Teste singular: a contagem de `fct_leituras` tem que ser igual à de `stg_leituras`. |

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

**Atenção ao atualizar:** quem já rodou o `int_leituras_enriquecidas` antes tem a view antiga no schema `analytics`. Agora ela é criada no schema `intermediate`. Para apagar a antiga: `DROP VIEW IF EXISTS analytics.int_leituras_enriquecidas;`.

Depois, no banco:

```sql
SELECT id_maquina, medido_em, temperatura_ar_k, temperatura_ar_c FROM staging.stg_leituras LIMIT 5;
SELECT id_leitura, modos_falha, qtd_modos_falha FROM intermediate.int_leituras_enriquecidas WHERE qtd_modos_falha > 1 LIMIT 5;
SELECT id_maquina, fonte, total_leituras, total_falhas FROM marts.dim_maquina ORDER BY total_falhas DESC;
SELECT count(*) FROM marts.fct_leituras;
SELECT d.fonte, count(*) AS leituras, count(*) FILTER (WHERE f.houve_falha) AS falhas
FROM marts.fct_leituras f
JOIN marts.dim_maquina d USING (id_maquina)
GROUP BY d.fonte;
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

`dbt build` cria 4 views + 2 tabelas e executa os testes: `Done. PASS=54 WARN=0 ERROR=0 SKIP=0 TOTAL=54` (6 modelos + 48 testes). Com a carga padrão: `stg_leituras` / `int_leituras_enriquecidas` / `fct_leituras` = 24.511 linhas; `dim_maquina` = 18 linhas (soma de `total_leituras` = 24.511).
Se um teste falhar, o dbt mostra qual e quantas linhas violaram a regra.
