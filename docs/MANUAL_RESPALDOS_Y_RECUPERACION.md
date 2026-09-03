# Manual de Respaldos Semanales y Recuperación ante Desastres (SGV-UTEQ)

**Sistema de Gestión de Vinculación con la Sociedad (SGV)**  
**Universidad Técnica Estatal de Quevedo (UTEQ)**  
**Estándar de Seguridad y Disponibilidad - Auditoría CACES**

---

## 1. Política Institucional de Respaldos
- **Frecuencia:** Semanal (Todos los Domingos a las 02:00 AM).
- **Herramienta:** `pg_dump` con compresión de nivel máximo `gzip -9`.
- **Formato:** Archivo binario comprimido `.sql.gz` con marca de tiempo ISO.
- **Ubicación de Almacenamiento en Servidor:** `/home/ubuntu/backups_db/`
- **Política de Retención Inteligente:** Conserva automáticamente los últimos **4 respaldos semanales** (28 días de historial seguro). Los respaldos con más de 28 días se depuran automáticamente para no saturar el almacenamiento en AWS EC2.
- **Tamaño promedio:** ~425 KB por archivo semanal (~1.7 MB mensual total).

---

## 2. Cron Job Automatizado Activo
El servicio corre de forma nativa en el crontab del servidor Linux de producción:

```bash
0 2 * * 0 /home/ubuntu/app/scripts/backup_semanal_db.sh >> /home/ubuntu/backups_db/cron.log 2>&1
```

---

## 3. Comandos Rápidos de Gestión

### A. Generar un Respaldo Manual en Cualquier Momento (On-Demand)
Si vas a realizar una sustentación, auditoría o cambio masivo y deseas asegurar la base de datos de inmediato:

```bash
cd /home/ubuntu/app
bash scripts/backup_semanal_db.sh
```

### B. Listar Respaldos Existentes y Espacio Ocupado
```bash
ls -lh /home/ubuntu/backups_db
```

### C. Ver el Registro de Auditoría de Respaldos
```bash
cat /home/ubuntu/backups_db/backup.log
```

### D. Restaurar la Base de Datos ante Desastres
Para recuperar la base de datos completa a partir del respaldo más reciente:
```bash
cd /home/ubuntu/app
bash scripts/restaurar_db.sh
```
O especificar un archivo puntual:
```bash
bash scripts/restaurar_db.sh /home/ubuntu/backups_db/sgv_uteq_backup_20260903_013549.sql.gz
```

---

*Documento auditado y versionado para acreditación institucional UTEQ.*
