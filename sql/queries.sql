-- Consultas de exemplo (CTEs e window functions). Rode com:  make queries
-- (equivale a: docker compose exec -T postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB" < sql/queries.sql)
-- As séries "SIM-xx" têm uma leitura a cada 5 min; as "AI4I-xx" são máquinas virtuais (ver README).

-- 1) Taxa de falha por fonte e tipo de produto -------------------------------------------------
SELECT m.fonte,
       l.tipo_produto,
       count(*)                                   AS leituras,
       count(*) FILTER (WHERE l.falha)            AS falhas,
       round(100.0 * avg(l.falha::int), 2)        AS taxa_falha_pct
FROM leituras l
JOIN maquinas m USING (maquina_id)
GROUP BY m.fonte, l.tipo_produto
ORDER BY m.fonte, l.tipo_produto;

-- 2) Ranking de máquinas por número de falhas (RANK + percentual do total) ----------------------
WITH por_maquina AS (
    SELECT maquina_id,
           count(*)                        AS leituras,
           count(*) FILTER (WHERE falha)   AS falhas
    FROM leituras
    GROUP BY maquina_id
)
SELECT maquina_id,
       leituras,
       falhas,
       round(100.0 * falhas / leituras, 2)                              AS taxa_falha_pct,
       rank() OVER (ORDER BY falhas DESC)                               AS posicao,
       round(100.0 * falhas / sum(falhas) OVER (), 1)                   AS pct_das_falhas_totais
FROM por_maquina
ORDER BY posicao, maquina_id;

-- 3) Média móvel das últimas 12 leituras (~1 h, se não houver lacunas) da temperatura de processo -----------
SELECT maquina_id,
       ts,
       temp_processo_k,
       round(avg(temp_processo_k) OVER (
           PARTITION BY maquina_id ORDER BY ts
           ROWS BETWEEN 11 PRECEDING AND CURRENT ROW
       )::numeric, 2) AS media_movel_12
FROM leituras
WHERE maquina_id = 'SIM-01'
ORDER BY ts
LIMIT 50;

-- 4) Detecção de salto: variação do torque em relação à leitura anterior (LAG) -------------------
WITH variacao AS (
    SELECT maquina_id, ts, torque_nm,
           torque_nm - lag(torque_nm) OVER (PARTITION BY maquina_id ORDER BY ts) AS delta_torque
    FROM leituras
    WHERE maquina_id LIKE 'SIM-%'
)
SELECT maquina_id, ts, torque_nm, round(delta_torque::numeric, 1) AS delta_torque
FROM variacao
WHERE abs(delta_torque) > 25
ORDER BY abs(delta_torque) DESC
LIMIT 20;

-- 5) Modos de falha por máquina, com a posição de cada modo dentro da máquina (ROW_NUMBER) ------
WITH contagem AS (
    SELECT l.maquina_id, f.modo, count(*) AS ocorrencias
    FROM falhas f
    JOIN leituras l USING (leitura_id)
    GROUP BY l.maquina_id, f.modo
)
SELECT maquina_id, modo, ocorrencias,
       row_number() OVER (PARTITION BY maquina_id ORDER BY ocorrencias DESC, modo) AS posicao_na_maquina
FROM contagem
ORDER BY maquina_id, posicao_na_maquina;

-- 6) Tempo entre falhas consecutivas por máquina (LAG sobre as leituras com falha) ----------------
WITH eventos AS (
    SELECT maquina_id, ts,
           lag(ts) OVER (PARTITION BY maquina_id ORDER BY ts) AS ts_falha_anterior
    FROM leituras
    WHERE falha
)
SELECT maquina_id,
       count(*) FILTER (WHERE ts_falha_anterior IS NOT NULL)                         AS intervalos,
       avg(ts - ts_falha_anterior)                                                   AS tempo_medio_entre_falhas,
       min(ts - ts_falha_anterior)                                                   AS menor_intervalo
FROM eventos
GROUP BY maquina_id
HAVING count(*) FILTER (WHERE ts_falha_anterior IS NOT NULL) > 0
ORDER BY tempo_medio_entre_falhas;

-- 7) Falha por faixa de desgaste da ferramenta (NTILE em quartis) ---------------------------------
WITH quartis AS (
    SELECT falha, desgaste_min,
           ntile(4) OVER (ORDER BY desgaste_min) AS quartil_desgaste
    FROM leituras
)
SELECT quartil_desgaste,
       min(desgaste_min) AS desgaste_min_do_quartil,
       max(desgaste_min) AS desgaste_max_do_quartil,
       count(*)          AS leituras,
       round(100.0 * avg(falha::int), 2) AS taxa_falha_pct
FROM quartis
GROUP BY quartil_desgaste
ORDER BY quartil_desgaste;

-- 8) Falhas por dia com acumulado (soma acumulada por janela) -------------------------------------
WITH diario AS (
    SELECT ts::date AS dia, count(*) FILTER (WHERE falha) AS falhas
    FROM leituras
    WHERE maquina_id LIKE 'SIM-%'
    GROUP BY 1
)
SELECT dia, falhas,
       sum(falhas) OVER (ORDER BY dia) AS falhas_acumuladas
FROM diario
ORDER BY dia;
