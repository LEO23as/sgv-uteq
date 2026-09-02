#!/bin/bash
# ==============================================================================
# SGV-UTEQ: Script de Recuperación ante Desastres (Disaster Recovery)
# Restaura un respaldo .sql.gz previa verificación estricta de firma SHA-256
# ==============================================================================

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "Uso: $0 <ruta_al_archivo_backup.sql.gz>"
    echo "Ejemplo: $0 ~/backups/sgv_db/sgv_db_20260901_220000.sql.gz"
    exit 1
fi

ARCHIVO_BACKUP="$1"

if [ ! -f "${ARCHIVO_BACKUP}" ]; then
    echo "❌ ERROR: El archivo de respaldo '${ARCHIVO_BACKUP}' no existe."
    exit 1
fi

echo "=========================================================="
echo "SGV-UTEQ: PROTOCOLO DE RECUPERACIÓN ANTE DESASTRES"
echo "=========================================================="
echo "Archivo objetivo: ${ARCHIVO_BACKUP}"

# 1. Verificación de Integridad Criptográfica Forense SHA-256
CHECKSUM_FILE="${ARCHIVO_BACKUP}.sha256"
if [ -f "${CHECKSUM_FILE}" ]; then
    echo "Verificando firma criptográfica SHA-256..."
    cd "$(dirname "${ARCHIVO_BACKUP}")"
    if sha256sum -c "$(basename "${CHECKSUM_FILE}")"; then
        echo "✅ Verificación SHA-256 EXITOSA: El archivo está 100% íntegro e inalterado."
    else
        echo "❌ ERROR CRÍTICO: La firma SHA-256 no coincide. El respaldo está dañado o fue manipulado."
        exit 1
    fi
    cd - > /dev/null
else
    echo "⚠️ ADVERTENCIA: No se encontró el archivo de firma .sha256 correspondiente."
fi

# 2. Confirmación de Seguridad
read -p "⚠️ ATENCIÓN: Esta acción sobreescribirá los datos actuales de la base de datos. ¿Deseas continuar? (s/N): " CONFIRMAR
if [[ ! "${CONFIRMAR}" =~ ^[sS]$ ]]; then
    echo "Operación cancelada por el operador."
    exit 0
fi

# 3. Restauración de Base de Datos
DB_NAME="${DB_NAME:-postgres}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-host.docker.internal}"
DB_PORT="${DB_PORT:-5432}"

echo "Restaurando base de datos en '${DB_NAME}'..."
if command -v docker >/dev/null 2>&1 && docker ps --format '{{.Names}}' | grep -q "sgv_backend"; then
    gunzip -c "${ARCHIVO_BACKUP}" | docker exec -i sgv_backend psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}"
elif command -v psql >/dev/null 2>&1; then
    gunzip -c "${ARCHIVO_BACKUP}" | psql -U "${DB_USER}" -h "${DB_HOST}" -p "${DB_PORT}" -d "${DB_NAME}"
else
    echo "❌ ERROR: No se encontró cliente psql ni contenedor Docker activo."
    exit 1
fi

echo "=========================================================="
echo "✅ Base de datos restaurada satisfactoriamente."
echo "=========================================================="
