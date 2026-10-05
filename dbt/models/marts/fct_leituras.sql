-- Fato de leituras: uma linha por leitura de sensores (o "que aconteceu").
--
-- O que é um fato?
-- Em modelagem dimensional, o fato registra eventos/medidas (aqui, cada leitura).
-- A dimensão (dim_maquina) descreve a máquina; o fato aponta para ela via id_maquina.
-- Consultas tipicamente filtram/agrupam pela dimensão e somam/contam o fato.
--
-- Grain: exatamente 1 linha por id_leitura (mesma contagem de stg_leituras /
-- int_leituras_enriquecidas). Os modos de falha já vêm agregados (modos_falha,
-- qtd_modos_falha), então leituras com vários modos não se duplicam.

select
    id_leitura,
    id_maquina,
    medido_em,
    tipo_produto,
    temperatura_ar_c,
    temperatura_processo_c,
    rotacao_rpm,
    torque_nm,
    desgaste_min,
    houve_falha,
    modos_falha,
    qtd_modos_falha
from {{ ref('int_leituras_enriquecidas') }}
