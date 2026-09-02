#!/bin/bash
# ==============================================================================
# SGV-UTEQ: Script de Respaldo Semanal Automatizado y Rotación de Base de Datos
# Estándar de Disponibilidad, Resiliencia y Gobernanza de Datos (CACES / LOES)
# ==============================================================================

set -euo pipefail

# 1. Configuración de Directorios y Variables
BACKUP_DIR="${HOME}/backups/sgv_db"
FECHA=$(date +"%Y%m%d_%H%M%S")
ARCHIVO_BACKUP="${BACKUP_DIR}/sgv_db_semanal_${FECHA}.sql.gz"
# Retención de 30 días (mantiene las últimas 4 semanas de respaldos históricos)
DIAS_RETENCION=30

# Parámetros de conexión a la Base de Datos
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-host.docker.internal}"
DB_PORT="${DB_PORT:-5432}"

mkdir -p "${BACKUP_DIR}"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Iniciando respaldo semanal institucional de base de datos '${DB_NAME}'..."

# 2. Extraer y Comprimir con gzip (nivel 9 máximo)
if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "sgv_backend"; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Modo: Extracción a través de contenedor Docker 'sgv_backend'..."
    docker exec -i sgv_backend pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" --clean --if-exists | gzip -9 > "${ARCHIVO_BACKUP}"
elif command -v pg_dump >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Modo: Extracción mediante cliente nativo 'pg_dump'..."
    pg_dump -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}" --clean --if-exists | gzip -9 > "${ARCHIVO_BACKUP}"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR CRÍTICO: No se encontró 'pg_dump' ni contenedor Docker activo."
    exit 1
fi

# 3. Firma Criptográfica SHA-256 (Integridad Forense CACES)
if [ -f "${ARCHIVO_BACKUP}" ] && [ -s "${ARCHIVO_BACKUP}" ]; then
    sha256sum "${ARCHIVO_BACKUP}" > "${ARCHIVO_BACKUP}.sha256"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Respaldo semanal generado con éxito: ${ARCHIVO_BACKUP}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')]    Firma SHA-256 calculada y certificada exitosamente."
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ERROR: El archivo de respaldo se generó vacío o no existe."
    exit 1
fi

# 4. Poda automática (Política de retención de 30 días / 4 semanas de histórico)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Aplicando política de retención (eliminando respaldos > ${DIAS_RETENCION} días)..."
find "${BACKUP_DIR}" -type f \( -name "*.sql.gz" -o -name "*.sha256" \) -mtime +${DIAS_RETENCION} -delete
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Política de retención de ${DIAS_RETENCION} días aplicada correctamente."
