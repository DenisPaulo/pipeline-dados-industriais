-- Teste singular: o dbt considera que o teste FALHA se a consulta devolver alguma linha.
-- Aqui: dim_maquina deve ter exatamente uma linha por máquina do staging
-- (nenhuma máquina perdida pelo left join / group by, nenhuma inventada).
with contagens as (

    select
        (select count(*) from {{ ref('stg_maquinas') }}) as qtd_staging,
        (select count(*) from {{ ref('dim_maquina') }}) as qtd_mart

)

select *
from contagens
where qtd_staging <> qtd_mart
