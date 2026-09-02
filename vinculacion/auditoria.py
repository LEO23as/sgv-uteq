"""
Módulo de Auditoría Criptográfica Inmutable (Estándar UTEQ - Módulo G)
Implementa encadenamiento criptográfico con SHA-256 para trazabilidad antifraude.
"""
import hashlib
import json
from django.utils import timezone
from .models import BitacoraAuditoria

GENESIS_HASH = '0' * 64


def _calcular_hash(hash_anterior, entidad, id_registro, accion, usuario_id, username, detalles_str, creado_en_str):
    payload = f'{hash_anterior}|{entidad}|{id_registro}|{accion}|{usuario_id}|{username}|{detalles_str}|{creado_en_str}'
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def registrar_auditoria(entidad, id_registro, accion, detalles=None, request=None, usuario=None):
    """
    Registra un evento encadenado criptográficamente.
    Garantiza la trazabilidad del operador (username, usuario_id, IP de red).
    """
    try:
        from .models import Usuario

        # Determinar usuario e IP
        usuario_id = None
        username = 'SISTEMA'
        ip_origen = '127.0.0.1'

        if request:
            usuario_id = request.session.get('usuario_id')
            username = (
                request.session.get('username') or 
                request.session.get('usuario_username') or 
                request.session.get('usuario_nombre')
            )
            # Si tenemos el ID de usuario pero no el username exacto en sesión, consultarlo en BD
            if usuario_id and (not username or username in ('ANONIMO', 'SISTEMA')):
                try:
                    u = Usuario.objects.filter(id_usuario=usuario_id).first()
                    if u:
                        username = u.username or u.nombres
                except Exception:
                    pass

            if not username and hasattr(request, 'user') and request.user.is_authenticated:
                username = getattr(request.user, 'username', 'SISTEMA')
                usuario_id = getattr(request.user, 'id_usuario', getattr(request.user, 'id', None))

            if not username:
                username = 'SISTEMA'

            ip_origen = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1')).split(',')[0].strip()
        elif usuario:
            usuario_id = getattr(usuario, 'id_usuario', None)
            username = getattr(usuario, 'username', None) or getattr(usuario, 'nombres', 'SISTEMA')

        # Formatear detalles
        detalles_str = json.dumps(detalles, ensure_ascii=False, default=str) if detalles else '{}'

        # Obtener el último hash de la cadena
        ultimo_evento = BitacoraAuditoria.objects.order_by('-id_bitacora').first()
        hash_anterior = ultimo_evento.hash_actual if ultimo_evento else GENESIS_HASH

        evento = BitacoraAuditoria(
            entidad=entidad,
            id_registro=id_registro,
            accion=accion,
            detalles_json=detalles_str,
            usuario_id=usuario_id,
            username=username,
            ip_origen=ip_origen,
            hash_anterior=hash_anterior,
        )
        evento.save()

        # Calcular nuevo hash con el timestamp exacto persistido
        creado_en_str = evento.creado_en.strftime('%Y-%m-%d %H:%M:%S') if evento.creado_en else timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        hash_actual = _calcular_hash(
            hash_anterior=hash_anterior,
            entidad=entidad,
            id_registro=id_registro,
            accion=accion,
            usuario_id=usuario_id,
            username=username,
            detalles_str=detalles_str,
            creado_en_str=creado_en_str,
        )
        evento.hash_actual = hash_actual
        evento.save(update_fields=['hash_actual'])
        return evento
    except Exception as e:
        # No bloquear la transacción principal si la auditoría falla
        import logging
        logging.getLogger(__name__).error(f"Error al registrar auditoría: {e}")
        return None


def verificar_integridad_cadena():
    """
    Recorre toda la bitácora verificando que cada eslabón esté intacto.
    Detecta manipulaciones manuales en la base de datos (inyección T1-T5 del PDF).
    """
    eventos = list(BitacoraAuditoria.objects.order_by('id_bitacora'))
    if not eventos:
        return {'valido': True, 'total_eventos': 0, 'mensaje': 'Bitácora vacía (sin eventos aún)'}

    hash_esperado_anterior = GENESIS_HASH
    errores = []

    for ev in eventos:
        # 1. Validar encadenamiento con el bloque anterior
        if ev.hash_anterior != hash_esperado_anterior:
            errores.append({
                'id_bitacora': ev.id_bitacora,
                'error': 'Ruptura de encadenamiento con bloque anterior',
                'hash_anterior_guardado': ev.hash_anterior,
                'hash_esperado': hash_esperado_anterior,
            })

        # 2. Recalcular hash de los datos del bloque actual
        creado_en_str = ev.creado_en.strftime('%Y-%m-%d %H:%M:%S') if ev.creado_en else ''
        hash_recalculado = _calcular_hash(
            hash_anterior=ev.hash_anterior,
            entidad=ev.entidad,
            id_registro=ev.id_registro,
            accion=ev.accion,
            usuario_id=ev.usuario_id,
            username=ev.username,
            detalles_str=ev.detalles_json or '{}',
            creado_en_str=creado_en_str,
        )

        if hash_recalculado != ev.hash_actual:
            errores.append({
                'id_bitacora': ev.id_bitacora,
                'error': 'Manipulación de datos detectada en el registro',
                'hash_guardado': ev.hash_actual,
                'hash_recalculado': hash_recalculado,
            })

        hash_esperado_anterior = ev.hash_actual

    return {
        'valido': len(errores) == 0,
        'total_eventos': len(eventos),
        'errores': errores,
        'ultimo_hash': hash_esperado_anterior,
    }
