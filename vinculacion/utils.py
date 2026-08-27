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
    """Envía correo con diseño institucional y credenciales de acceso al nuevo usuario."""
    asunto = 'Acceso al Sistema de Gestión y Georreferenciación de Vinculación (SGV UTEQ)'
    
    # Versión en texto plano
    mensaje_texto = f"""
Estimado/a {nombres},

Se ha generado su cuenta de acceso al Sistema de Gestión y Georreferenciación de Vinculación (SGV) de la Universidad Técnica Estatal de Quevedo (UTEQ).

Sus credenciales de acceso son:
  • Usuario: {username}
  • Contraseña Temporal: {password_temporal}
  • Enlace de Acceso: http://18.227.201.40:5174/

IMPORTANTE:
Por políticas de seguridad institucional, al iniciar sesión por primera vez el sistema le solicitará cambiar obligatoriamente su contraseña temporal por una definitiva.

Atentamente,
Dirección de Vinculación con la Sociedad
Universidad Técnica Estatal de Quevedo (UTEQ)
    """

    # Versión HTML Institucional UTEQ
    mensaje_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
      <meta charset="UTF-8">
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; margin: 0; padding: 20px; }}
        .email-container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }}
        .header {{ background-color: #1b7a2b; color: #ffffff; padding: 25px 30px; text-align: center; }}
        .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }}
        .header p {{ margin: 5px 0 0; font-size: 13px; opacity: 0.9; }}
        .content {{ padding: 30px; color: #334155; line-height: 1.6; font-size: 15px; }}
        .saludo {{ font-size: 16px; font-weight: 600; color: #0f172a; margin-bottom: 12px; }}
        .credentials-card {{ background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 10px; padding: 18px 22px; margin: 20px 0; }}
        .cred-row {{ margin-bottom: 10px; font-size: 14px; }}
        .cred-row:last-child {{ margin-bottom: 0; }}
        .cred-label {{ font-weight: 700; color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 2px; }}
        .cred-value {{ font-family: monospace; font-size: 16px; font-weight: 700; color: #1b7a2b; background: #e8f5e9; padding: 4px 8px; border-radius: 5px; display: inline-block; }}
        .cred-value-pass {{ font-family: monospace; font-size: 16px; font-weight: 700; color: #7c3aed; background: #f5f3ff; padding: 4px 8px; border-radius: 5px; display: inline-block; border: 1px dashed #c4b5fd; }}
        .btn-container {{ text-align: center; margin: 25px 0; }}
        .btn-login {{ background-color: #1b7a2b; color: #ffffff !important; text-decoration: none; padding: 12px 28px; border-radius: 25px; font-weight: 700; font-size: 15px; display: inline-block; box-shadow: 0 4px 10px rgba(27,122,43,0.25); }}
        .alert-box {{ background-color: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #92400e; margin-top: 20px; }}
        .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 18px 30px; text-align: center; font-size: 12px; color: #64748b; }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="header">
          <h1>SGV | UTEQ</h1>
          <p>Sistema de Gestión y Georreferenciación de Vinculación</p>
        </div>
        <div class="content">
          <div class="saludo">Estimado/a {nombres},</div>
          <p>Se ha generado exitosamente su cuenta de acceso institucional para el <strong>Sistema de Gestión de Vinculación con la Sociedad (SGV)</strong> de la Universidad Técnica Estatal de Quevedo.</p>
          
          <div class="credentials-card">
            <div class="cred-row">
              <span class="cred-label">Nombre de Usuario:</span>
              <span class="cred-value">{username}</span>
            </div>
            <div class="cred-row">
              <span class="cred-label">Contraseña Temporal:</span>
              <span class="cred-value-pass">{password_temporal}</span>
            </div>
          </div>

          <div class="btn-container">
            <a href="http://18.227.201.40:5174/" class="btn-login" target="_blank">Acceder al Sistema SGV</a>
          </div>

          <div class="alert-box">
            <strong>⚠️ Cambio de clave obligatorio:</strong> Por políticas de seguridad de la UTEQ, al iniciar sesión por primera vez el sistema le solicitará cambiar obligatoriamente su contraseña temporal por una personal definitiva.
          </div>
        </div>
        <div class="footer">
          <strong>Dirección de Vinculación con la Sociedad</strong><br>
          Universidad Técnica Estatal de Quevedo (UTEQ)<br>
          <em>Este es un correo automático de seguridad, por favor no responda a este mensaje.</em>
        </div>
      </div>
    </body>
    </html>
    """

    try:
        from_email = settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER or 'soporte.vinculacion@uteq.edu.ec'
        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=from_email,
            recipient_list=[correo],
            html_message=mensaje_html,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f'Error enviando correo: {e}')
        return False