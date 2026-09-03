import os
import django
from datetime import date
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from vinculacion.models import PeriodoAcademico, Proyecto

# 1. Definir Periodos Académicos Oficiales
PERIODOS_DEF = [
    {
        "codigo": "SPA 2023-2024",
        "nombre": "Segundo Período Académico 2023-2024",
        "tipo": "SPA",
        "fecha_inicio": date(2023, 10, 1),
        "fecha_fin": date(2024, 3, 31),
        "activo": False,
    },
    {
        "codigo": "PPA 2024-2025",
        "nombre": "Primer Período Académico 2024-2025",
        "tipo": "PPA",
        "fecha_inicio": date(2024, 5, 1),
        "fecha_fin": date(2024, 9, 30),
        "activo": False,
    },
    {
        "codigo": "SPA 2024-2025",
        "nombre": "Segundo Período Académico 2024-2025",
        "tipo": "SPA",
        "fecha_inicio": date(2024, 10, 1),
        "fecha_fin": date(2025, 3, 31),
        "activo": False,
    },
    {
        "codigo": "PPA 2025-2026",
        "nombre": "Primer Período Académico 2025-2026",
        "tipo": "PPA",
        "fecha_inicio": date(2025, 5, 1),
        "fecha_fin": date(2025, 9, 30),
        "activo": False,
    },
    {
        "codigo": "SPA 2025-2026",
        "nombre": "Segundo Período Académico 2025-2026",
        "tipo": "SPA",
        "fecha_inicio": date(2025, 10, 1),
        "fecha_fin": date(2026, 3, 31),
        "activo": True,  # Período Vigente
    },
    {
        "codigo": "PPA 2026-2027",
        "nombre": "Primer Período Académico 2026-2027",
        "tipo": "PPA",
        "fecha_inicio": date(2026, 5, 1),
        "fecha_fin": date(2026, 9, 30),
        "activo": False,
    },
]

print("=== REGISTRANDO PERIODOS ACADÉMICOS ===")
periodos_map = {}
for pdef in PERIODOS_DEF:
    pobj, created = PeriodoAcademico.objects.update_or_create(
        codigo=pdef["codigo"],
        defaults={
            "nombre": pdef["nombre"],
            "tipo": pdef["tipo"],
            "fecha_inicio": pdef["fecha_inicio"],
            "fecha_fin": pdef["fecha_fin"],
            "activo": pdef["activo"],
            "creado_en": timezone.now()
        }
    )
    periodos_map[pdef["codigo"]] = pobj
    estado = "CREADO" if created else "ACTUALIZADO"
    print(f"  [{pobj.id_periodo}] {pobj.codigo} - {pobj.nombre} ({estado}) | Activo: {pobj.activo}")

spa_2526 = periodos_map["SPA 2025-2026"]
ppa_2627 = periodos_map["PPA 2026-2027"]
ppa_2425 = periodos_map["PPA 2024-2025"]
spa_2425 = periodos_map["SPA 2024-2025"]
ppa_2526 = periodos_map["PPA 2025-2026"]
spa_2324 = periodos_map["SPA 2023-2024"]

print("\n=== ASIGNANDO PERÍODO INICIO Y FIN A LOS 55 PROYECTOS ===")
actualizados = 0

for proy in Proyecto.objects.all():
    aprob = proy.fecha_aprobacion
    
    # Determinar periodo inicio según fecha de aprobación oficial
    if not aprob or aprob.year <= 2023:
        p_ini = spa_2324
    elif aprob < date(2024, 7, 1):
        p_ini = ppa_2425
    elif aprob < date(2025, 1, 1):
        p_ini = spa_2425
    elif aprob < date(2025, 7, 1):
        p_ini = ppa_2526
    else:
        p_ini = spa_2526
        
    # Fin planificado:
    # Si fue aprobado en 2025, su vigencia de 2 años se extiende a PPA 2026-2027
    # Si fue aprobado en 2023 o 2024, culmina en SPA 2025-2026
    if aprob and aprob.year >= 2025:
        p_fin = ppa_2627
    else:
        p_fin = spa_2526
        
    proy.id_periodo_inicio = p_ini
    proy.id_periodo_fin = p_fin
    proy.save()
    actualizados += 1

print(f"\nTotal Proyectos actualizados con su ciclo multianual: {actualizados}")

print("\n=== DISTRIBUCIÓN FINAL DE PROYECTOS POR PERÍODO DE INICIO ===")
for pobj in PeriodoAcademico.objects.all().order_by('fecha_inicio'):
    n_ini = Proyecto.objects.filter(id_periodo_inicio=pobj).count()
    n_activos = Proyecto.objects.filter(id_periodo_inicio=pobj) | Proyecto.objects.filter(id_periodo_fin=pobj)
    print(f"  {pobj.codigo}: {n_ini} proyectos iniciados | {n_activos.distinct().count()} con actividad en el ciclo")
