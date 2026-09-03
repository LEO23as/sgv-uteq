"""
Script institucional SGV-UTEQ:
Clasificación y vinculación masiva de ODS para todos los proyectos de vinculación.
Analiza nombre, carrera, facultad, línea de vinculación, programa y descripción.
"""
import os
import re
import unicodedata
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from vinculacion.models import Proyecto

def normalizar(txt):
    if not txt:
        return ""
    txt = unicodedata.normalize('NFKD', str(txt)).encode('ASCII', 'ignore').decode('utf-8')
    return txt.lower()

# Reglas semánticas por ODS (Pesos e indicadores clave)
REGLAS_ODS = {
    1: ['pobreza', 'vulnerable', 'vulnerabilidad', 'escasos recursos', 'asistencia social', 'apoyo comunitario', 'inclusion social', 'familias vulnerables', 'marginal'],
    2: ['hidropon', 'huert', 'seguridad alimentaria', 'hortaliz', 'nutricion', 'agroecol', 'agronom', 'agricola', 'cultivo', 'pecuari', 'ganader', 'suelo', 'soberania alimentaria', 'desnutricion', 'fertiliz', 'cosecha', 'aliment', 'produccion agropecuaria', 'bovino', 'porcino', 'avicol', 'cacao', 'platano', 'maiz', 'arroz'],
    3: ['salud', 'bienestar', 'enfermedad', 'zoonosis', 'clinica', 'medicin', 'enfermer', 'higiene', 'ergonom', 'primeros auxilios', 'salud mental', 'bioseguridad', 'parasit', 'vacun', 'postura', 'nutricional'],
    4: ['educaci', 'capacitaci', 'taller', 'alfabetiz', 'escuela', 'colegio', 'bachillerato', 'ensenanza', 'aprendizaje', 'pedagog', 'competencia', 'robotica educativa', 'tutori', 'estudiante', 'docente', 'formacion tecnica', 'educativo', 'formacion continua', 'ludico'],
    5: ['mujer', 'genero', 'empoderamiento femenino', 'liderazgo femenino', 'violencia intrafamiliar', 'equidad', 'madres'],
    6: ['agua', 'potable', 'cuenca', 'hidric', 'saneamiento', 'rio', 'estero', 'drenaje', 'residual', 'calidad del agua', 'abastecimiento'],
    7: ['energia', 'solar', 'fotovoltaic', 'renovable', 'biomasa', 'electric', 'eficiencia energetica', 'panel solar'],
    8: ['emprendimiento', 'microempresa', 'pyme', 'negocio', 'contabil', 'finanza', 'tribut', 'asociativ', 'empleo', 'turismo', 'comercializ', 'productiv', 'costo', 'administraci', 'mercado', 'artesanal', 'desarrollo economico'],
    9: ['software', 'aplicacion movil', 'automatiz', 'sistema web', 'infraestructura', 'tecnolog', 'redes', 'sensor', 'iot', 'transformacion digital', 'informacion', 'computacion', 'plataforma web', 'desarrollo tecnologico', 'ingenieria'],
    10: ['desigualdad', 'accesibilidad', 'adulto mayor', 'discapacidad', 'derechos', 'inclusivo', 'grupos de atencion prioritaria', 'equidad social'],
    11: ['ordenamiento territorial', 'catastro', 'comunidad sostenible', 'movilidad', 'gestion de riesgo', 'resiliencia', 'urban', 'espacio publico', 'asentamiento', 'prevencion de desastres', 'seguridad vial'],
    12: ['recicl', 'residuo', 'desecho', 'compost', 'economia circular', 'buenas practicas agricolas', 'bpa', 'postcosecha', 'biodegradable', 'consumo responsable', 'organico', 'manejo de residuos'],
    13: ['cambio climatico', 'huella de carbono', 'mitigacion', 'adaptacion', 'resiliencia climatica', 'meteorol', 'calentamiento global'],
    14: ['acuicol', 'acuicultur', 'peces', 'tilapia', 'piscicol', 'camaron', 'pesca', 'estuario', 'rio', 'ecosistema acuatico'],
    15: ['biodiversidad', 'flora', 'fauna', 'bosque', 'especie nativa', 'reforestaci', 'vivero', 'conservacion', 'silvicultur', 'entomol', 'ecosistema terrestre', 'arbol', 'forestal', 'area protegida'],
    16: ['paz', 'justicia', 'gobernanza', 'fortalecimiento institucional', 'juridic', 'transparencia', 'participacion ciudadana', 'derecho', 'legal', 'institucion'],
    17: ['alianza', 'convenio', 'articulacion', 'cooperacion interinstitucional', 'gad', 'vinculacion con la sociedad', 'desarrollo local', 'agenda 2030']
}

def clasificar_proyecto(p):
    texto = " ".join([
        p.nombre or "",
        p.nombre_corto or "",
        p.linea_vinculacion or "",
        p.programa or "",
        p.area_conocimiento or "",
        p.sub_area_conocimiento or "",
        p.descripcion or "",
        p.objetivo_general or "",
        p.id_carrera.nombre if p.id_carrera else "",
        p.id_facultad.nombre if p.id_facultad else "",
    ])
    norm = normalizar(texto)

    puntuaciones = {}
    for ods_num, keywords in REGLAS_ODS.items():
        score = 0
        for kw in keywords:
            if kw in norm:
                # Si está en el título principal da más peso
                if kw in normalizar(p.nombre or ""):
                    score += 3
                else:
                    score += 1
        if score > 0:
            puntuaciones[ods_num] = score

    if not puntuaciones:
        # Por defecto vinculación universitaria apoya educación y alianzas
        return [4, 17]

    # Ordenar por mayor coincidencia y tomar los top 1 a 3 ODS
    ordenados = sorted(puntuaciones.items(), key=lambda x: x[1], reverse=True)
    top_ods = [item[0] for item in ordenados[:3]]
    return sorted(top_ods)

def main():
    proyectos = Proyecto.objects.all().select_related('id_carrera', 'id_facultad')
    total = proyectos.count()
    print(f"=== CLASIFICANDO {total} PROYECTOS DE VINCULACIÓN UTEQ ===")

    actualizados = 0
    distribucion = {i: 0 for i in range(1, 18)}

    for p in proyectos:
        ods_detectados = clasificar_proyecto(p)
        cadena_ods = ", ".join(f"ODS {num}" for num in ods_detectados)
        p.ods = cadena_ods
        p.save(update_fields=['ods'])
        actualizados += 1

        for num in ods_detectados:
            distribucion[num] += 1

        print(f"[{p.codigo}] {p.nombre[:55]}... -> {cadena_ods}")

    print("\n=== RESUMEN DE PROYECTOS POR ODS ===")
    for num, cant in distribucion.items():
        print(f"ODS {num:2d}: {cant:2d} proyectos vinculados")

    print(f"\n¡Proceso completado! Se actualizaron {actualizados} proyectos en la base de datos.")

if __name__ == '__main__':
    main()
