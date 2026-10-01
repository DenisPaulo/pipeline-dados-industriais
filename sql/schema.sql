-- Esquema normalizado do pipeline. Idempotente: pode ser executado várias vezes.
-- As faixas dos CHECKs espelham FAIXAS_FISICAS em src/pipeline/schemas.py.

CREATE TABLE IF NOT EXISTS maquinas (
    maquina_id  TEXT PRIMARY KEY,
    fonte       TEXT NOT NULL CHECK (fonte IN ('ai4i', 'simulado')),
    criada_em   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS leituras (
    leitura_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    maquina_id       TEXT NOT NULL REFERENCES maquinas (maquina_id),
    ts               TIMESTAMP NOT NULL,
    tipo_produto     CHAR(1) NOT NULL CHECK (tipo_produto IN ('L', 'M', 'H')),
    temp_ar_k        DOUBLE PRECISION NOT NULL CHECK (temp_ar_k BETWEEN 250 AND 350),
    temp_processo_k  DOUBLE PRECISION NOT NULL CHECK (temp_processo_k BETWEEN 250 AND 400),
    rotacao_rpm      INTEGER NOT NULL CHECK (rotacao_rpm BETWEEN 0 AND 10000),
    torque_nm        DOUBLE PRECISION NOT NULL CHECK (torque_nm BETWEEN 0 AND 200),
    desgaste_min     INTEGER NOT NULL CHECK (desgaste_min BETWEEN 0 AND 1000),
    falha            BOOLEAN NOT NULL,
    -- chave natural: base da carga idempotente (ON CONFLICT)
    CONSTRAINT uq_leituras_maquina_ts UNIQUE (maquina_id, ts)
);

CREATE TABLE IF NOT EXISTS falhas (
    falha_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    leitura_id  BIGINT NOT NULL REFERENCES leituras (leitura_id) ON DELETE CASCADE,
    modo        TEXT NOT NULL CHECK (modo IN ('TWF', 'HDF', 'PWF', 'OSF', 'RNF', 'DESCONHECIDO')),
    CONSTRAINT uq_falhas_leitura_modo UNIQUE (leitura_id, modo)
);

-- Índices (o UNIQUE de leituras já cobre buscas por máquina + intervalo de tempo)
CREATE INDEX IF NOT EXISTS ix_leituras_ts ON leituras (ts);
CREATE INDEX IF NOT EXISTS ix_leituras_falha ON leituras (maquina_id, ts) WHERE falha;
CREATE INDEX IF NOT EXISTS ix_falhas_modo ON falhas (modo);
