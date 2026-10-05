-- Teste singular: o dbt considera que o teste FALHA se a consulta devolver alguma linha.
-- Aqui: fct_leituras deve ter exatamente a mesma contagem de stg_leituras
-- (nenhuma leitura perdida nem inventada ao materializar o mart).
with contagens as (

    select
        (select count(*) from {{ ref('stg_leituras') }}) as qtd_staging,
        (select count(*) from {{ ref('fct_leituras') }}) as qtd_mart

)

select *
from contagens
where qtd_staging <> qtd_mart
