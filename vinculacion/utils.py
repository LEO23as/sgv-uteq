import bcrypt
import random
import string
import unicodedata
from django.core.mail import send_mail
from django.conf import settings


def quitar_tildes(texto):
    """Elimina tildes y caracteres especiales."""
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def generar_username(nombres, apellidos):
    """
    Genera username institucional: 
    2 primeras letras del nombre + 1er apellido completo + 1ª letra del 2º apellido
    Ejemplo: Pedro Castro López → pecastrol
    """
    from vinculacion.models import Usuario
    
    nombres_split = nombres.strip().split()
    apellidos_split = apellidos.strip().split()
    
    # 2 primeras letras del nombre (ej: "pe" de "Pedro")
    nombre_limpio = quitar_tildes(nombres_split[0]).lower() if nombres_split else 'us'
    prefijo_nombre = nombre_limpio[:2] if len(nombre_limpio) >= 2 else nombre_limpio
    
    # Primer apellido completo (ej: "castro")
    apellido1 = quitar_tildes(apellidos_split[0]).lower() if len(apellidos_split) > 0 else 'usuario'
    
    # Primera letra del segundo apellido (ej: "l" de "López")
    primera_apellido2 = quitar_tildes(apellidos_split[1][0]).lower() if len(apellidos_split) > 1 else ''
    
    username_base = f"{prefijo_nombre}{apellido1}{primera_apellido2}"
    username = username_base
    
    # Verificar duplicados
    contador = 2
    while Usuario.objects.filter(username=username).exists():
        username = f'{username_base}{contador}'
        contador += 1
    
    return username


def generar_password_temporal():
    """Genera contraseña temporal segura de 10 caracteres."""
    mayusculas = random.choice(string.ascii_uppercase)
    numeros = ''.join(random.choices(string.digits, k=3))
    simbolo = random.choice('@#$%')
    minusculas = ''.join(random.choices(string.ascii_lowercase, k=5))
    
    password = list(mayusculas + numeros + simbolo + minusculas)
    random.shuffle(password)
    return ''.join(password)


def hashear_password(password_plano):
    """Hashea la contraseña con bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_plano.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verificar_password(password_plano, password_hash):
    """Verifica contraseña contra el hash bcrypt."""
    return bcrypt.checkpw(
        password_plano.encode('utf-8'),
        password_hash.encode('utf-8')
    )


def enviar_credenciales(correo, nombres, username, password_temporal):
    """Envía correo con credenciales de acceso al nuevo usuario."""
    asunto = 'Credenciales de Acceso - Sistema de Gestión de Vinculación (SGV UTEQ)'
    mensaje = f"""
Estimado/a {nombres},

Se ha generado su cuenta de acceso al Sistema de Gestión de Vinculación (SGV) de la Universidad Técnica Estatal de Quevedo (UTEQ).

Sus credenciales de acceso son:

  • Usuario: {username}
  • Contraseña Temporal: {password_temporal}
  • Enlace del Sistema: http://18.227.201.40:5174/

IMPORTANTE:
Por motivos de seguridad institucional, al iniciar sesión por primera vez el sistema le solicitará cambiar obligatoriamente su contraseña temporal por una personal y definitiva.

Si usted no solicitó este acceso o presenta algún inconveniente, comuníquese con el Departamento de Vinculación con la Colectividad.

Atentamente,
Departamento de Vinculación con la Colectividad
Universidad Técnica Estatal de Quevedo (UTEQ)
    """
    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL or 'soporte.vinculacion@uteq.edu.ec',
            [correo],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Error enviando correo: {e}')
        return False