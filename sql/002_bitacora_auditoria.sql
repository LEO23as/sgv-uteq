-- ============================================================================
--  Bitácora de Auditoría Criptográfica Inmutable (Estándar UTEQ - Módulo G)
-- ============================================================================

CREATE TABLE IF NOT EXISTS bitacora_auditoria (
    id_bitacora    SERIAL PRIMARY KEY,
    entidad        VARCHAR(60) NOT NULL DEFAULT 'PROYECTO',
    id_registro    INTEGER NOT NULL,
    accion         VARCHAR(50) NOT NULL,
    detalles_json  TEXT,
    usuario_id     INTEGER,
    username       VARCHAR(100),
    ip_origen      VARCHAR(45),
    hash_anterior  VARCHAR(64) NOT NULL,
    hash_actual    VARCHAR(64) NOT NULL,
    creado_en      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_bitacora_hash ON bitacora_auditoria(hash_actual);
CREATE INDEX IF NOT EXISTS idx_bitacora_registro ON bitacora_auditoria(entidad, id_registro);
