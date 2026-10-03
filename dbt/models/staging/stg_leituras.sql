-- Staging de leituras: nomes claros e temperaturas também em Celsius (além de Kelvin).
-- Celsius = Kelvin - 273,15; arredondado em 2 casas (round exige numeric no PostgreSQL).
select
    leitura_id as id_leitura,
    maquina_id as id_maquina,
    ts as medido_em,
    tipo_produto,

    temp_ar_k as temperatura_ar_k,
    round((temp_ar_k - 273.15)::numeric, 2) as temperatura_ar_c,
    temp_processo_k as temperatura_processo_k,
    round((temp_processo_k - 273.15)::numeric, 2) as temperatura_processo_c,

    rotacao_rpm,
    torque_nm,
    desgaste_min,
    falha as houve_falha
from {{ source('pipeline', 'leituras') }}
