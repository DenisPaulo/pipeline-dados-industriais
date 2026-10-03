-- Staging de falhas: uma linha por (leitura, modo de falha).
select
    falha_id as id_falha,
    leitura_id as id_leitura,
    modo as modo_falha
from {{ source('pipeline', 'falhas') }}
