#!/bin/bash
# ==============================================================================
# SGV-UTEQ: Script de Respaldo Automatizado y Rotación de Base de Datos
# Estándar de Disponibilidad y Gobernanza de Datos (CACES / LOES)
# ==============================================================================

set -euo pipefail

# 1. Configuración de Directorios y Variables
BACKUP_DIR="${HOME}/backups/sgv_db"
LOG_FILE="${BACKUP_DIR}/backup.log"
FECHA=$(date +"%Y%m%d_%H%M%S")
ARCHIVO_BACKUP="${BACKUP_DIR}/sgv_db_${FECHA}.sql.gz"
DIAS_RETENCION=7

# Parámetros de conexión a la Base de Datos (toma del entorno o defaults)
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

mkdir -p "${BACKUP_DIR}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "=========================================================="
log "Iniciando respaldo de base de datos '${DB_NAME}'..."

# 2. Ejecución del Respaldo Comprimido
# Si corre dentro del servidor con Docker, usa el contenedor si está activo
if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "sgv_backend"; then
    log "Modo: Extracción a través de contenedor Docker 'sgv_backend'..."
    docker exec -i sgv_backend pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" --clean --if-exists --no-owner --no-privileges | gzip -9 > "${ARCHIVO_BACKUP}"
elif command -v pg_dump >/dev/null 2>&1; then
    log "Modo: Extracción mediante cliente nativo 'pg_dump'..."
    pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" --clean --if-exists --no-owner --no-privileges | gzip -9 > "${ARCHIVO_BACKUP}"
else
    log "ERROR CRÍTICO: No se encontró 'pg_dump' ni contenedor Docker activo."
    exit 1
fi

# 3. Validación de Integridad del Archivo Generado
if [ -f "${ARCHIVO_BACKUP}" ] && [ -s "${ARCHIVO_BACKUP}" ]; then
    TAMANIO=$(du -h "${ARCHIVO_BACKUP}" | cut -f1)
    # Generar Hash SHA-256 para verificación criptográfica de integridad forense
    HASH_SHA256=$(sha256sum "${ARCHIVO_BACKUP}" | cut -d' ' -f1)
    echo "${HASH_SHA256}  $(basename "${ARCHIVO_BACKUP}")" > "${ARCHIVO_BACKUP}.sha256"
    
    log "✅ Respaldo generado con éxito: ${ARCHIVO_BACKUP}"
    log "   Tamaño: ${TAMANIO}"
    log "   Hash SHA-256: ${HASH_SHA256}"
else
    log "❌ ERROR: El archivo de respaldo se generó vacío o no existe."
    exit 1
fi

# 4. Política de Retención y Poda (Auto-rotación de 7 días)
log "Aplicando política de retención (eliminando respaldos > ${DIAS_RETENCION} días)..."
BORRADOS=$(find "${BACKUP_DIR}" -type f \( -name "*.sql.gz" -o -name "*.sha256" \) -mtime +${DIAS_RETENCION} -print -delete | wc -l)
log "Respaldos antiguos depurados: ${BORRADOS} archivo(s)."

TOTAL_RESPALDOS=$(find "${BACKUP_DIR}" -type f -name "*.sql.gz" | wc -l)
log "Total de respaldos vigentes en disco: ${TOTAL_RESPALDOS}"
log "Respaldo concluido satisfactoriamente."
log "=========================================================="
