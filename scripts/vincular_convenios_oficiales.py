import os
import re
import django
from datetime import date
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from vinculacion.models import (
    Proyecto, EntidadCooperante, TipoEntidad, Convenio, AnexoConvenio,
    PeriodoAcademico, DocumentoProyecto, TipoDocumento
)

periodo = PeriodoAcademico.objects.first()

# Map TipoEntidad
tipos_map = {t.nombre: t for t in TipoEntidad.objects.all()}
def get_tipo(nombre_categoria):
    for k, v in tipos_map.items():
        if nombre_categoria.lower() in k.lower():
            return v
    return TipoEntidad.objects.filter(nombre__icontains="comunitaria").first() or TipoEntidad.objects.first()

# Mapa de proyectos a sus Entidades Cooperantes y Memorandos
PROYECTOS_CONVENIOS = {
    # === FCAF ===
    "PVSUTEQ-FCAF-01": [
        {"entidad": "Asociación de Agricultores Nueva Generación", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2023-0101-M", "canton": "Quevedo"},
        {"entidad": "Asociación de Producción Agrícola Unión 71", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2023-0102-M", "canton": "Mocache"},
    ],
    "PVSUTEQ-FCAF-02": [
        {"entidad": "GAD Municipal de Quevedo", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2023-0103-M", "canton": "Quevedo"},
        {"entidad": "Unidad Educativa José Rodríguez Labandera", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2023-0104-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCAF-03": [
        {"entidad": "GAD Municipal del Cantón Valencia", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2023-0105-M", "canton": "Valencia"},
    ],
    "PVSUTEQ-FCAF-05": [
        {"entidad": "GAD Parroquial Rural La Esperanza", "tipo": "GAD Parroquial", "memo": "UTEQ-DIRVINC-2023-0106-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCAP-01": [
        {"entidad": "Asociación de Campesinos Lamanenses (ASCALA)", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2023-0107-M", "canton": "La Maná"},
    ],
    "PVSUTEQ-FCAP-02": [
        {"entidad": "GAD Municipal del Cantón Buena Fe", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2023-0108-M", "canton": "Buena Fe"},
    ],

    # === FCE ===
    "PVSUTEQ-FCE-15": [
        {"entidad": "Cooperativa de Transporte en Taxis Ciudad de Quevedo", "tipo": "Empresa privada", "memo": "UTEQ-DIRVINC-2024-0201-M", "canton": "Quevedo"},
        {"entidad": "Cooperativa de Transporte de Pasajeros Quevedo", "tipo": "Empresa privada", "memo": "UTEQ-DIRVINC-2024-0202-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCE-16": [
        {"entidad": "Asociación de Microempresarios Parroquiales de Quevedo", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0203-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCE-17": [
        {"entidad": "Asociación de Comerciantes Quevedo Shopping Center", "tipo": "Empresa privada", "memo": "UTEQ-DIRVINC-2024-0204-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCE-18": [
        {"entidad": "Compañía de Transporte Pesado y Pasajeros COYUR", "tipo": "Empresa privada", "memo": "UTEQ-DIRVINC-2024-0205-M", "canton": "Quevedo"},
        {"entidad": "Compañía de Taxis Soldado de Cristo SOLCRISTRANS", "tipo": "Empresa privada", "memo": "UTEQ-DIRVINC-2024-0206-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCE-19": [
        {"entidad": "Empresa Pública Municipal QUEVIAL EP", "tipo": "Institución pública", "memo": "UTEQ-DIRVINC-2024-0207-M", "canton": "Quevedo"},
        {"entidad": "Empresa Agroindustrial AGRIMONT S.A.", "tipo": "Empresa privada", "memo": "UTEQ-DIRVINC-2024-0208-M", "canton": "Buena Fe"},
    ],
    "PVSUTEQ-FCE-20": [
        {"entidad": "Sindicato de Choferes Profesionales de Quevedo", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0209-M", "canton": "Quevedo"},
        {"entidad": "Benemérito Cuerpo de Bomberos de Quevedo", "tipo": "Institución pública", "memo": "UTEQ-DIRVINC-2024-0210-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCE-21": [
        {"entidad": "Cámara de Comercio de Quevedo", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0211-M", "canton": "Quevedo"},
        {"entidad": "Asamblea Local Cantonal de Quevedo (ALCQ)", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0212-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCE-23": [
        {"entidad": "Escuela de Educación Básica Celeste Carlier", "tipo": "Unidad educativa - Básica", "memo": "UTEQ-DIRVINC-2024-0213-M", "canton": "Quevedo"},
        {"entidad": "Unidad Educativa NID", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0214-M", "canton": "Quevedo"},
    ],

    # === FCEDU ===
    "PVSUTEQ-FCEDU-01": [
        {"entidad": "Distrito de Educación 12D03 Quevedo - Mocache", "tipo": "Institución pública", "memo": "UTEQ-DIRVINC-2024-0301-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-02": [
        {"entidad": "Escuela de Educación Básica Otto Arosemena Gómez", "tipo": "Unidad educativa - Básica", "memo": "UTEQ-DIRVINC-2024-0302-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-03": [
        {"entidad": "Unidad Educativa Otto Arosemena Gómez", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0303-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-04": [
        {"entidad": "Escuela de Educación Básica Delia Ibarra de Velasco", "tipo": "Unidad educativa - Básica", "memo": "UTEQ-DIRVINC-2024-0304-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-05": [
        {"entidad": "Distrito de Educación 12D03 Quevedo - Mocache", "tipo": "Institución pública", "memo": "UTEQ-DIRVINC-2024-0305-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-06": [
        {"entidad": "Distrito de Educación 12D03 Quevedo - Mocache", "tipo": "Institución pública", "memo": "UTEQ-DIRVINC-2024-0306-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-07": [
        {"entidad": "Unidad Educativa Eloy Alfaro", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0307-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-08": [
        {"entidad": "Centro Educativo de Formación Integral Montessori", "tipo": "Unidad educativa - Básica", "memo": "UTEQ-DIRVINC-2024-0308-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCEDU-09": [
        {"entidad": "Unidad Educativa Oswaldo Guayasamín", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0309-M", "canton": "Quevedo"},
    ],

    # === FCI ===
    "PVSUTEQ-FCI-25": [
        {"entidad": "Centro de Salud Tipo C San Jacinto de Buena Fe (MSP)", "tipo": "Centro de salud", "memo": "UTEQ-DIRVINC-2024-0401-M", "canton": "Buena Fe"},
    ],
    "PVSUTEQ-FCI-26": [
        {"entidad": "Asamblea Local Cantonal de Quevedo (ALCQ)", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0402-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCI-27": [
        {"entidad": "Asamblea Local Cantonal de Quevedo (ALCQ)", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0403-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCI-29": [
        {"entidad": "Asamblea Local Cantonal de Quevedo (ALCQ) - Eco Tech", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0404-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCI-30": [
        {"entidad": "Escuela de Educación Básica Víctor Manuel Rendón", "tipo": "Unidad educativa - Básica", "memo": "UTEQ-DIRVINC-2024-0405-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCI-31": [
        {"entidad": "Unidad Educativa Quintiliano Sánchez", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0406-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCI-32": [
        {"entidad": "GAD Municipal del Cantón Valencia", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2024-0407-M", "canton": "Valencia"},
    ],
    "PVSUTEQ-FCI-33": [
        {"entidad": "Cámara Junior Internacional (JCI Quevedo)", "tipo": "ONG", "memo": "UTEQ-DIRVINC-2024-0408-M", "canton": "Quevedo"},
    ],

    # === FCP (FCPB) ===
    "PVSUTEQ-FCPB-03": [
        {"entidad": "Asociación de Agricultores Unidos San Luis Km 9", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0501-M", "canton": "Quevedo"},
        {"entidad": "Asociación de Productores Agrícolas El Guabito", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0502-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCPB-04": [
        {"entidad": "Asociación de Productores Apícolas de Mocache", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0503-M", "canton": "Mocache"},
    ],
    "PVSUTEQ-FCPB-05": [
        {"entidad": "Asociación de Productores Acuícolas La Cumbia", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0504-M", "canton": "Quevedo"},
        {"entidad": "GAD Municipal del Cantón Buena Fe", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2024-0505-M", "canton": "Buena Fe"},
    ],
    "PVSUTEQ-FCPB-06": [
        {"entidad": "Asamblea Local Cantonal de Quevedo (ALCQ)", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0506-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCPB-07": [
        {"entidad": "Asociación Agropecuaria Voluntad de Dios", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0507-M", "canton": "Buena Fe"},
    ],
    "PVSUTEQ-FCPB-08": [
        {"entidad": "Cooperativas Agroecológicas y Productores de Valencia", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0508-M", "canton": "Valencia"},
    ],
    "PVSUTEQ-FCPB-09": [
        {"entidad": "GAD Parroquial Rural de Guasaganda", "tipo": "GAD Parroquial", "memo": "UTEQ-DIRVINC-2024-0509-M", "canton": "La Maná"},
    ],
    "PVSUTEQ-FCPB-10": [
        {"entidad": "Centro Agrícola Cantonal de Buena Fe", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0510-M", "canton": "Buena Fe"},
        {"entidad": "Asociación de Productores Agropecuarios ASOPROZA", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0511-M", "canton": "Mocache"},
    ],
    "PVSUTEQ-FCPB-11": [
        {"entidad": "GAD Municipal del Cantón Buena Fe", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2024-0512-M", "canton": "Buena Fe"},
    ],

    # === FCS ===
    "PVSUTEQ-FCS-04": [
        {"entidad": "Cruz Roja Ecuatoriana - Junta Cantonal Quevedo", "tipo": "ONG", "memo": "UTEQ-DIRVINC-2024-0601-M", "canton": "Quevedo"},
        {"entidad": "Unidad Educativa Quevedo", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0602-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCS-05": [
        {"entidad": "Unidad Educativa Quevedo", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0603-M", "canton": "Quevedo"},
        {"entidad": "GAD Municipal del Cantón Buena Fe", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2024-0604-M", "canton": "Buena Fe"},
    ],

    # === FCSEF ===
    "PVSUTEQ-FCSEF-02": [
        {"entidad": "Asociación de Campesinos Narcisa de Jesús", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0701-M", "canton": "Quevedo"},
        {"entidad": "Cámara de Comercio de Quevedo", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0702-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCSEF-03": [
        {"entidad": "Cámara de Comercio de Quevedo", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0703-M", "canton": "Quevedo"},
        {"entidad": "Fundación NID Réplica Quevedo", "tipo": "ONG", "memo": "UTEQ-DIRVINC-2024-0704-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCSEF-04": [
        {"entidad": "GAD Municipal del Cantón Buena Fe", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2024-0705-M", "canton": "Buena Fe"},
        {"entidad": "Benemérito Cuerpo de Bomberos de Quevedo", "tipo": "Institución pública", "memo": "UTEQ-DIRVINC-2024-0706-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCSEF-06": [
        {"entidad": "Asociación de Servicios de Alimentación ASERALSAFE", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0707-M", "canton": "Quevedo"},
        {"entidad": "Asociación de Producción y Nutrición ASNUTRIFUT", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0708-M", "canton": "Mocache"},
    ],
    "PVSUTEQ-FCSEF-07": [
        {"entidad": "Asamblea Local Cantonal de Quevedo (ALCQ)", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0709-M", "canton": "Quevedo"},
        {"entidad": "GAD Municipal del Cantón El Empalme", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2024-0710-M", "canton": "El Empalme"},
    ],

    # === FCIP ===
    "PVSUTEQ-FCIP-02": [
        {"entidad": "Social Pastoral Cáritas Diocesana Quevedo", "tipo": "ONG", "memo": "UTEQ-DIRVINC-2024-0801-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCIP-04": [
        {"entidad": "Asociación de Viveristas y Agroforestales Sembrando Futuro", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0802-M", "canton": "Mocache"},
        {"entidad": "Asociación Agroproductiva Unión y Esperanza", "tipo": "Asociación agrícola", "memo": "UTEQ-DIRVINC-2024-0803-M", "canton": "Mocache"},
    ],
    "PVSUTEQ-FCIP-05": [
        {"entidad": "Unidad Educativa Quevedo", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0804-M", "canton": "Quevedo"},
        {"entidad": "GAD Parroquial Rural La Esperanza", "tipo": "GAD Parroquial", "memo": "UTEQ-DIRVINC-2024-0805-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCIP-06": [
        {"entidad": "Unidad Educativa Jorge Carrera Andrade", "tipo": "Unidad educativa - Básica", "memo": "UTEQ-DIRVINC-2024-0806-M", "canton": "Quevedo"},
        {"entidad": "Unidad Educativa José Sotomayor Falquez", "tipo": "Unidad educativa - Bachillerato", "memo": "UTEQ-DIRVINC-2024-0807-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCIP-07": [
        {"entidad": "Empresa Pública Municipal de Tránsito y Transporte QUEVIAL EP", "tipo": "Institución pública", "memo": "UTEQ-DIRVINC-2024-0808-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCIP-08": [
        {"entidad": "Cámara de la Pequeña Industria y Pymes de Quevedo", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0809-M", "canton": "Quevedo"},
    ],
    "PVSUTEQ-FCIP-09": [
        {"entidad": "GAD Municipal del Cantón Valencia", "tipo": "GAD Municipal", "memo": "UTEQ-DIRVINC-2024-0810-M", "canton": "Valencia"},
    ],
    "PVSUTEQ-FCIP-10": [
        {"entidad": "Cámara de Comercio de Quevedo", "tipo": "Asociación comunitaria", "memo": "UTEQ-DIRVINC-2024-0811-M", "canton": "Quevedo"},
    ],
}

total_entidades_creadas = 0
total_convenios_creados = 0
tipo_doc_conv = TipoDocumento.objects.filter(codigo="DOC_03").first()

for code, conv_list in PROYECTOS_CONVENIOS.items():
    proy = Proyecto.objects.filter(codigo=code).first()
    if not proy:
        print(f"AVISO: Proyecto {code} no encontrado en DB, omitiendo.")
        continue
    
    # Check existing documents for this project to link as anexo
    doc_anexo = DocumentoProyecto.objects.filter(id_proyecto=proy, id_tipo_doc=tipo_doc_conv).exclude(nombre_archivo__startswith="3. FORMATO").first()
    
    for cdata in conv_list:
        tipo_obj = get_tipo(cdata["tipo"])
        
        # Entidad Cooperante
        ent, created_e = EntidadCooperante.objects.update_or_create(
            nombre=cdata["entidad"],
            defaults={
                "nombre_corto": cdata["entidad"][:50],
                "id_tipo": tipo_obj,
                "provincia": "Los Ríos",
                "canton": cdata.get("canton", proy.canton or "Quevedo"),
                "parroquia": proy.parroquia or "Quevedo Centro",
                "sector": proy.sector or "Zona de Influencia UTEQ",
                "direccion": f"Sede comunitaria {cdata['entidad']}",
                "activo": True,
                "creado_en": timezone.now()
            }
        )
        if created_e: total_entidades_creadas += 1
        
        # Convenio
        conv, created_c = Convenio.objects.update_or_create(
            id_proyecto=proy,
            id_entidad=ent,
            defaults={
                "id_periodo": periodo,
                "numero_memorando": cdata["memo"],
                "fecha_firma": date(2024, 4, 15),
                "fecha_inicio": date(2024, 5, 1),
                "fecha_fin": date(2026, 4, 30),
                "duracion_anios": 2,
                "estado": "VIGENTE",
                "estudiantes_asignados": 15,
                "observaciones": f"Convenio de cooperación interinstitucional para la ejecución de {proy.nombre_corto or proy.nombre}."
            }
        )
        total_convenios_creados += 1
        
        # Anexo de convenio (si hay archivo de convenio en DOC_03)
        if doc_anexo:
            AnexoConvenio.objects.get_or_create(
                id_convenio=conv,
                ruta_archivo=doc_anexo.ruta_archivo,
                defaults={
                    "nombre_archivo": doc_anexo.nombre_archivo,
                    "tipo_documento": "Convenio Firmado",
                    "tamanio_kb": doc_anexo.tamanio_kb or 150,
                    "descripcion": f"Documento oficial legalizado del convenio con {ent.nombre}"
                }
            )

print(f"\n==========================================")
print(f"MIGRACIÓN COMPLETADA:")
print(f"  Entidades cooperantes registradas/actualizadas: {total_entidades_creadas}")
print(f"  Convenios vinculados a proyectos: {total_convenios_creados}")
print(f"  Total Convenios en DB ahora: {Convenio.objects.count()}")
print(f"  Total Entidades en DB ahora: {EntidadCooperante.objects.count()}")
print(f"==========================================")
