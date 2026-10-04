-- Leituras enriquecidas: cada leitura com a fonte da máquina e os modos de falha juntos.
--
-- Por que existe a CTE `falhas_por_leitura`?
-- Uma leitura pode ter MAIS DE UM modo de falha (na carga atual, 29 leituras têm mais de um
-- modo e uma delas tem 3), então stg_falhas tem várias linhas por leitura. Se juntássemos
-- stg_leituras com stg_falhas direto, essas leituras apareceriam repetidas (uma linha por modo)
-- e qualquer contagem ou média nos marts ficaria errada.
-- Por isso agregamos as falhas ANTES do join: uma linha por leitura, com os modos numa só
-- coluna de texto (ex.: 'HDF, PWF') e a quantidade de modos.
-- O teste tests/int_leituras_enriquecidas_sem_duplicacao.sql garante que a conta fecha.

with falhas_por_leitura as (

    select
        id_leitura,
        string_agg(modo_falha, ', ' order by modo_falha) as modos_falha,
        count(*) as qtd_modos_falha
    from {{ ref('stg_falhas') }}
    group by id_leitura

)

select
    l.id_leitura,
    l.id_maquina,
    m.fonte,
    l.medido_em,
    l.houve_falha,
    f.modos_falha,
    coalesce(f.qtd_modos_falha, 0) as qtd_modos_falha,

    -- Colunas de sensores (adicionadas para os marts; as colunas acima são as originais)
    l.tipo_produto,
    l.temperatura_ar_c,
    l.temperatura_processo_c,
    l.rotacao_rpm,
    l.torque_nm,
    l.desgaste_min
from {{ ref('stg_leituras') }} as l
join {{ ref('stg_maquinas') }} as m
    on m.id_maquina = l.id_maquina
left join falhas_por_leitura as f
    on f.id_leitura = l.id_leitura
