-- Fato agregado: falhas por máquina e por dia.
--
-- Agrega as leituras com falha (houve_falha) de fct_leituras numa linha por
-- (máquina, data). qtd_falhas = quantas leituras com falha naquele dia;
-- modos_falha lista os conjuntos de modos distintos do dia (separados por '; ').
-- Útil para série temporal e ranking diário sem varrer todas as leituras.

select
    id_maquina,
    medido_em::date as data_ref,
    count(*) as qtd_falhas,
    string_agg(distinct modos_falha, '; ' order by modos_falha) as modos_falha
from {{ ref('fct_leituras') }}
where houve_falha
group by id_maquina, medido_em::date
