-- Teste singular de VOLUME: o total de leituras da última carga não pode cair mais que
-- 10% em relação à carga anterior (ex.: uma fonte que parou de chegar).
-- Na primeira carga não há "anterior", então o teste passa.
-- A tolerância pode ser trocada com --vars '{queda_maxima: 0.2}'.
with ultimas as (
    select
        total_leituras,
        row_number() over (order by carga_id desc) as ordem
    from {{ source('pipeline', 'cargas') }}
),

atual as (select total_leituras from ultimas where ordem = 1),
anterior as (select total_leituras from ultimas where ordem = 2)

select
    anterior.total_leituras as total_anterior,
    atual.total_leituras as total_atual
from atual cross join anterior
where atual.total_leituras < anterior.total_leituras * (1 - {{ var('queda_maxima', 0.1) }})
