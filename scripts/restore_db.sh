#!/bin/bash
# ==============================================================================
# SGV-UTEQ: Script de Recuperación ante Desastres (Disaster Recovery)
# Restaura un respaldo .sql.gz verificando su firma criptográfica SHA-256
# ==============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Uso: $0 <ruta_al_archivo_backup.sql.gz>"
    echo "Ejemplo: $0 ~/backups/sgv_db/sgv_db_20260901_220000.sql.gz"
    exit 1
fi

ARCHIVO_BACKUP="$1"

if [ ! -f "${ARCHIVO_BACKUP}" ]; then
    echo "❌ ERROR: El archivo '${ARCHIVO_BACKUP}' no existe."
    exit 1
fi

echo "=========================================================="
echo "SGV-UTEQ: PROTOCOLO DE RECUPERACIÓN DE BASE DE DATOS"
echo "=========================================================="
echo "Archivo a restaurar: ${ARCHIVO_BACKUP}"

# 1. Verificación de Integridad Criptográfica (si existe archivo .sha256)
CHECKSUM_FILE="${ARCHIVO_BACKUP}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    echo "Verificando integridad criptográfica SHA-256..."
    cd "$(dirname "${ARCHIVO_BACKUP}")"
    if sha256sum -c "$(basename "${CHECKSUM_FILE}")"; then
        echo "✅ Verificación SHA-256 EXITOSA. El archivo no ha sido corrompido ni alterado."
    else
        echo "❌ ERROR CRÍTICO: La firma criptográfica SHA-256 no coincide. Respaldo dañado o manipulado."
        exit 1
    fi
    cd - > /dev/null
fi

# 2. Confirmación de Seguridad
read -p "⚠️ ATENCIÓN: Esta acción sobreescribirá los datos actuales de la BD. ¿Deseas continuar? (s/N): " CONFIRMAR
if [[ ! "${CONFIRMAR}" =~ ^[sS]$ ]]; then
    echo "Operación cancelada por el usuario."
    exit 0
fi

# 3. Restauración
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Restaurando base de datos en '${DB_NAME}'..."
if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "sgv_backend"; then
    gunzip -c "${ARCHIVO_BACKUP}" | docker exec -i sgv_backend psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}"
elif command -v psql >/dev/null 2>&1; then
    gunzip -c "${ARCHIVO_BACKUP}" | psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}"
else
    echo "❌ ERROR: No se encontró cliente psql ni contenedor Docker."
    exit 1
fi

echo "=========================================================="
echo "✅ Base de datos restaurada satisfactoriamente."
echo "=========================================================="
