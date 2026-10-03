-- Staging de máquinas: só renomeia colunas para nomes claros (sem regra de negócio).
select
    maquina_id as id_maquina,
    fonte,
    criada_em
from {{ source('pipeline', 'maquinas') }}
