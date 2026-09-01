-- ============================================================================
--  Índices Compuestos de Alta Velocidad (Optimización de Carga Masiva)
--  UTEQ · Sistema de Gestión de Vinculación
-- ============================================================================

-- Índices en tabla PROYECTO (para acelerar filtros por período, facultad y estado)
CREATE INDEX IF NOT EXISTS idx_proyecto_periodo_fac ON proyecto(id_periodo_inicio, id_facultad);
CREATE INDEX IF NOT EXISTS idx_proyecto_fac_carrera ON proyecto(id_facultad, id_carrera);
CREATE INDEX IF NOT EXISTS idx_proyecto_estado ON proyecto(estado);
CREATE INDEX IF NOT EXISTS idx_proyecto_codigo ON proyecto(codigo);
CREATE INDEX IF NOT EXISTS idx_proyecto_fechas ON proyecto(fecha_inicio, fecha_fin_planificada);

-- Índices en tabla CONVENIO (búsqueda rápida por período y vigencia)
CREATE INDEX IF NOT EXISTS idx_convenio_periodo_est ON convenio(id_periodo, estado);
CREATE INDEX IF NOT EXISTS idx_convenio_proyecto ON convenio(id_proyecto);
CREATE INDEX IF NOT EXISTS idx_convenio_entidad ON convenio(id_entidad);

-- Índices en UBICACIONES Y DOCUMENTOS DEL PROYECTO
CREATE INDEX IF NOT EXISTS idx_ubicacion_proy_prin ON proyecto_ubicacion(id_proyecto, es_principal);
CREATE INDEX IF NOT EXISTS idx_doc_proy_tipo ON documento_proyecto(id_proyecto, id_tipo_doc);
CREATE INDEX IF NOT EXISTS idx_foto_proyecto ON foto_proyecto(id_proyecto);
