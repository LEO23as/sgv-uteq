#!/usr/bin/env bash
# ==============================================================================
# SGV-UTEQ: Instalador del Cron Job de Respaldo Semanal
# Configura la ejecución automática todos los Domingos a las 02:00 AM
# ==============================================================================

set -eo pipefail

APP_DIR="/home/ubuntu/app"
SCRIPT_BACKUP="${APP_DIR}/scripts/backup_semanal_db.sh"
SCRIPT_RESTORE="${APP_DIR}/scripts/restaurar_db.sh"
CRON_SCHEDULE="0 2 * * 0"
CRON_CMD="${SCRIPT_BACKUP} >> /home/ubuntu/backups_db/cron.log 2>&1"
CRON_LINE="${CRON_SCHEDULE} ${CRON_CMD}"

echo "========================================================"
echo "CONFIGURACIÓN DEL CRON JOB INSTITUCIONAL DE RESPALDOS"

# 1. Permisos de ejecución
chmod +x "${SCRIPT_BACKUP}" 2>/dev/null || true
chmod +x "${SCRIPT_RESTORE}" 2>/dev/null || true
echo "Permisos de ejecución otorgados a los scripts de respaldo."

# 2. Verificar si ya existe en crontab
CURRENT_CRON=$(crontab -l 2>/dev/null || echo "")

if echo "${CURRENT_CRON}" | grep -F "${SCRIPT_BACKUP}" > /dev/null; then
    echo "El cron job de respaldo semanal ya se encuentra instalado."
else
    (echo "${CURRENT_CRON}"; echo "${CRON_LINE}") | crontab -
    echo "Cron job semanal agregado con éxito:"
    echo "Horario: Todos los domingos a las 02:00 AM (America/Guayaquil)"
    echo "Comando: ${CRON_LINE}"
fi

echo "--------------------------------------------------------"
echo "Crontab activo actualmente para $(whoami):"
crontab -l
echo "========================================================"
