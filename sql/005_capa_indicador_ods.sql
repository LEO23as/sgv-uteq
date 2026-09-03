-- Tabla para almacenar los 17 Indicadores Oficiales ODS (Agenda 2030 CEPAL/ONU)
CREATE TABLE IF NOT EXISTS capa_indicador_ods (
    id_ods_indicador SERIAL PRIMARY KEY,
    ods_num INTEGER NOT NULL UNIQUE,
    nombre_ods VARCHAR(120) NOT NULL,
    codigo_indicador VARCHAR(60) NOT NULL,
    nombre_indicador TEXT NOT NULL,
    anio_reciente INTEGER NOT NULL,
    valor_reciente NUMERIC(10,2) NOT NULL,
    unidad VARCHAR(40) DEFAULT '%',
    fuente VARCHAR(200) NOT NULL,
    serie_historica JSONB DEFAULT '[]'::jsonb,
    activo BOOLEAN DEFAULT TRUE,
    fecha_carga TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_capa_ods_num ON capa_indicador_ods(ods_num);
