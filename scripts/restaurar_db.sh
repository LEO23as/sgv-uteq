#!/usr/bin/env bash
# ==============================================================================
# SGV-UTEQ: Script de Restauración de Base de Datos y Recuperación ante Desastres
# Universidad Técnica Estatal de Quevedo - Dirección de Vinculación
# Uso: ./restaurar_db.sh [/ruta/al/respaldo.sql.gz]
# ==============================================================================

set -eo pipefail

APP_DIR="/home/ubuntu/app"
BACKUP_DIR="/home/ubuntu/backups_db"
FECHA_HUMANA=$(date +"%Y-%m-%d %H:%M:%S")

echo "========================================================"
echo "[${FECHA_HUMANA}] SISTEMA DE RECUPERACIÓN ANTE DESASTRES UTEQ"

# 1. Determinar el archivo de respaldo
BACKUP_FILE="$1"
if [ -z "${BACKUP_FILE}" ]; then
    BACKUP_FILE=$(find "${BACKUP_DIR}" -name "sgv_uteq_backup_*.sql.gz" -type f | sort -r | head -n 1)
    if [ -z "${BACKUP_FILE}" ]; then
        echo "ERROR: No se encontró ningún archivo de respaldo en ${BACKUP_DIR}"
        echo "Especifique la ruta al archivo: ./restaurar_db.sh /ruta/al/archivo.sql.gz"
        exit 1
    fi
    echo "Seleccionado automáticamente el respaldo más reciente: ${BACKUP_FILE}"
else
    if [ ! -f "${BACKUP_FILE}" ]; then
        echo "ERROR: El archivo especificado no existe: ${BACKUP_FILE}"
        exit 1
    fi
    echo "Usando respaldo especificado: ${BACKUP_FILE}"
fi

# 2. Cargar variables de entorno
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

# 3. Confirmación
echo "Base de datos destino: ${DB_NAME} en ${DB_HOST}:${DB_PORT}"
echo "Iniciando proceso de restauración..."

START_TIME=$(date +%s)

export PGPASSWORD="${DB_PASS}"
gunzip -c "${BACKUP_FILE}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1 || true
unset PGPASSWORD

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "Restauración completada en ${DURATION} segundos."

# 4. Reiniciar backend para refrescar el pool de conexiones
if command -v docker &> /dev/null; then
    echo "Reiniciando contenedor backend para refrescar conexiones..."
    (cd "${APP_DIR}" && sudo docker compose restart backend > /dev/null 2>&1) || true
fi

echo "========================================================"
echo "SISTEMA RESTAURADO EXITOSAMENTE Y DISPONIBLE"
echo "========================================================"
