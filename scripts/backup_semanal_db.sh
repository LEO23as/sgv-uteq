#!/usr/bin/env bash
# ==============================================================================
# SGV-UTEQ: Script Institucional de Respaldo Semanal de Base de Datos PostgreSQL
# Universidad Técnica Estatal de Quevedo - Dirección de Vinculación
# Frecuencia recomendada: Semanal (Domingos 02:00 AM)
# Política de Retención: 4 semanas (rotación automática)
# ==============================================================================

set -eo pipefail

# 1. Rutas, Directorios y Políticas
APP_DIR="/home/ubuntu/app"
BACKUP_DIR="/home/ubuntu/backups_db"
LOG_FILE="${BACKUP_DIR}/backup.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
FECHA_HUMANA=$(date +"%Y-%m-%d %H:%M:%S")
BACKUP_FILE="${BACKUP_DIR}/sgv_uteq_backup_${TIMESTAMP}.sql.gz"
RETENTION_WEEKS=4
RETENTION_DAYS=$((RETENTION_WEEKS * 7))

mkdir -p "${BACKUP_DIR}"

log() {
    echo "[${FECHA_HUMANA}] $1" | tee -a "${LOG_FILE}"
}

log "========================================================"
log "INICIO DE RESPALDO SEMANAL DE BASE DE DATOS UTEQ"
log "Destino: ${BACKUP_FILE}"

# 2. Cargar variables de entorno si existen
if [ -f "${APP_DIR}/.env" ]; then
    DB_NAME=$(grep -E "^DB_NAME=" "${APP_DIR}/.env" | cut -d '=' -f2 | tr -d '\r"')
    DB_USER=$(grep -E "^DB_USER=" "${APP_DIR}/.env" | cut -d '=' -f2 | tr -d '\r"')
    DB_PASS=$(grep -E "^DB_PASSWORD=" "${APP_DIR}/.env" | cut -d '=' -f2 | tr -d '\r"')
    DB_PORT=$(grep -E "^DB_PORT=" "${APP_DIR}/.env" | cut -d '=' -f2 | tr -d '\r"')
fi

DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_PASS="${DB_PASS:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_HOST="127.0.0.1"

# 3. Ejecución de pg_dump con compresión gzip en streaming
log "Conectando a PostgreSQL en ${DB_HOST}:${DB_PORT} (Base: ${DB_NAME}, Usuario: ${DB_USER})..."

START_TIME=$(date +%s)

export PGPASSWORD="${DB_PASS}"
pg_dump \
    -h "${DB_HOST}" \
    -p "${DB_PORT}" \
    -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --clean \
    --if-exists \
    --no-owner \
    --no-privileges \
    | gzip -9 > "${BACKUP_FILE}"
unset PGPASSWORD

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 4. Verificación de Integridad del Archivo
if [ -f "${BACKUP_FILE}" ]; then
    FILESIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    BYTE_SIZE=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}" 2>/dev/null || echo 0)
    
    if [ "${BYTE_SIZE}" -gt 10000 ]; then
        log "RESPALDO COMPLETADO CON ÉXITO en ${DURATION} segundos."
        log "Archivo generado: ${BACKUP_FILE} (Tamaño: ${FILESIZE})"
    else
        log "ERROR CRÍTICO: El archivo generado es demasiado pequeño (${BYTE_SIZE} bytes). Posible fallo."
        exit 1
    fi
else
    log "ERROR CRÍTICO: No se pudo generar el archivo de respaldo."
    exit 1
fi

# 5. Política de Retención Inteligente (Conserva últimas 4 semanas)
log "Aplicando política de retención: conservando últimos ${RETENTION_WEEKS} respaldos semanales (${RETENTION_DAYS} días)..."
ELIMINADOS=0
while IFS= read -r archivo; do
    if [ -n "$archivo" ]; then
        log "Rotación: eliminando respaldo antiguo $(basename "$archivo")"
        rm -f "$archivo"
        ELIMINADOS=$((ELIMINADOS + 1))
    fi
done < <(find "${BACKUP_DIR}" -name "sgv_uteq_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS})

TOTAL_ACTUAL=$(find "${BACKUP_DIR}" -name "sgv_uteq_backup_*.sql.gz" -type f | wc -l)
log "Respaldos conservados en almacenamiento seguro: ${TOTAL_ACTUAL} archivos."
log "Espacio total ocupado por respaldos: $(du -sh "${BACKUP_DIR}" | cut -f1)"
log "FIN DEL PROCESO DE RESPALDO"
log "========================================================"
