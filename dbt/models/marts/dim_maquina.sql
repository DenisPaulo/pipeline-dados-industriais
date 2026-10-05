-- Dimensão de máquina: uma linha por máquina, com totais de leituras e falhas.
--
-- O que é uma dimensão?
-- Em modelagem dimensional (estilo star schema), a dimensão descreve "quem" ou "o quê"
-- (aqui, a máquina). Os fatos (fct_*) descrevem "o que aconteceu" (leituras, falhas).
-- Consultas tipicamente filtram/agrupam pela dimensão e somam os fatos.
--
-- Por que os totais aqui?
-- total_leituras e total_falhas são métricas agregadas por máquina, calculadas a partir
-- de int_leituras_enriquecidas. Assim o painel ou uma consulta rápida responde
-- "quantas leituras e falhas cada máquina teve" sem varrer todas as leituras de novo.
-- left join garante que máquinas sem leituras ainda aparecem (totais = 0).

select
    m.id_maquina,
    m.fonte,
    m.criada_em,
    count(l.id_leitura) as total_leituras,
    count(*) filter (where l.houve_falha) as total_falhas
from {{ ref('stg_maquinas') }} as m
left join {{ ref('int_leituras_enriquecidas') }} as l
    on l.id_maquina = m.id_maquina
group by m.id_maquina, m.fonte, m.criada_em
