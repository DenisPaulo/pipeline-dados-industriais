-- Teste singular de unicidade composta (id_maquina, data_ref).
-- Sem dbt_utils: devolve as chaves que aparecem mais de uma vez (deve ser 0 linhas).
select
    id_maquina,
    data_ref,
    count(*) as qtd
from {{ ref('fct_falhas_diarias') }}
group by id_maquina, data_ref
having count(*) > 1
