-- Teste singular: o dbt considera que o teste FALHA se a consulta devolver alguma linha.
-- Aqui: o nº de linhas de int_leituras_enriquecidas deve ser igual ao de stg_leituras
-- (nenhuma leitura duplicada por causa de várias falhas, nenhuma perdida pelo join com máquinas).
with contagens as (

    select
        (select count(*) from {{ ref('stg_leituras') }}) as qtd_staging,
        (select count(*) from {{ ref('int_leituras_enriquecidas') }}) as qtd_intermediate

)

select *
from contagens
where qtd_staging <> qtd_intermediate
