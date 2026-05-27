"""
utils/seguridad.py
Funciones reutilizables para todo el sistema de seguridad:
  - Validación de contraseñas fuertes
  - Control de intentos por email e IP
  - Gestión de tokens de sesión
  - Generación y envío de códigos 2FA
"""
import os
import re
import secrets
import string
import requests
from datetime import datetime, timedelta
from flask import request
from app_extensions import db, mail
from flask_mail import Message


# ─── Configuración ───────────────────────────────────────────────────────────

MAX_INTENTOS_EMAIL   = 3     # intentos antes de bloquear email
MAX_INTENTOS_IP      = 10    # intentos antes de bloquear IP
MAX_INTENTOS_2FA     = 5     # intentos antes de invalidar sesión 2FA
VENTANA_INTENTOS_MIN = 15    # minutos hacia atrás para contar intentos
BLOQUEO_EMAIL_MIN    = 10    # minutos de bloqueo de cuenta (reducido de 30 a 10)
BLOQUEO_IP_MIN       = 60    # minutos de bloqueo de IP
EXPIRACION_SESION_H  = 8     # horas de duración de sesión
EXPIRACION_2FA_MIN   = 10    # minutos de validez del código 2FA


# ─── Obtener IP real del visitante ───────────────────────────────────────────

def obtener_ip() -> str:
    """Obtiene la IP real considerando proxies."""
    # Proxy inverso estándar
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


# ─── Validación de contraseña fuerte ─────────────────────────────────────────

def validar_contrasena_fuerte(password: str) -> list[str]:
    """
    Retorna lista de errores. Lista vacía = contraseña válida.
    Reglas: mínimo 8 chars, mayúsculas, minúsculas, números, especiales.
    """
    errores = []
    if len(password) < 8:
        errores.append('Mínimo 8 caracteres.')
    if not re.search(r'[A-Z]', password):
        errores.append('Debe incluir al menos una letra MAYÚSCULA.')
    if not re.search(r'[a-z]', password):
        errores.append('Debe incluir al menos una letra minúscula.')
    if not re.search(r'\d', password):
        errores.append('Debe incluir al menos un número.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-\+\=\[\]\/\\;\'`~]', password):
        errores.append('Debe incluir al menos un carácter especial (!@#$%...).')
    return errores


# ─── Control de intentos fallidos ────────────────────────────────────────────

def _ventana_inicio() -> datetime:
    """Marca de tiempo de inicio de la ventana de análisis."""
    return datetime.utcnow() - timedelta(minutes=VENTANA_INTENTOS_MIN)


def contar_intentos_fallidos_email(email: str) -> int:
    """Cuenta intentos fallidos recientes para un email."""
    from models.seguridad import IntentoLogin
    return IntentoLogin.query.filter(
        IntentoLogin.email == email.lower(),
        IntentoLogin.exitoso == False,
        IntentoLogin.fecha >= _ventana_inicio()
    ).count()


def contar_intentos_fallidos_ip(ip: str) -> int:
    """Cuenta intentos fallidos recientes desde una IP."""
    from models.seguridad import IntentoLogin
    return IntentoLogin.query.filter(
        IntentoLogin.ip_address == ip,
        IntentoLogin.exitoso == False,
        IntentoLogin.fecha >= _ventana_inicio()
    ).count()


def registrar_intento(email: str, ip: str, exitoso: bool, motivo: str = None):
    """Graba un intento de login en la base de datos."""
    from models.seguridad import IntentoLogin
    intento = IntentoLogin(
        email=email.lower(),
        ip_address=ip,
        exitoso=exitoso,
        motivo_fallo=None if exitoso else (motivo or 'desconocido'),
        user_agent=request.headers.get('User-Agent', '')[:255],
    )
    db.session.add(intento)
    db.session.commit()


# ─── Bloqueos ─────────────────────────────────────────────────────────────────

def ip_esta_bloqueada(ip: str) -> bool:
    """True si la IP tiene un bloqueo activo y vigente."""
    from models.seguridad import BloqueoIP
    bloqueo = BloqueoIP.query.filter_by(ip_address=ip, activo=True).first()
    if not bloqueo:
        return False
    if bloqueo.esta_activo:
        return True
    # Expiró → desactivar
    bloqueo.activo = False
    db.session.commit()
    return False


def bloquear_ip(ip: str, motivo: str = 'Demasiados intentos fallidos'):
    """Bloquea una IP por BLOQUEO_IP_MIN minutos."""
    from models.seguridad import BloqueoIP
    existente = BloqueoIP.query.filter_by(ip_address=ip).first()
    expira = datetime.utcnow() + timedelta(minutes=BLOQUEO_IP_MIN)
    if existente:
        existente.activo         = True
        existente.motivo         = motivo
        existente.bloqueada_en   = datetime.utcnow()
        existente.desbloquear_en = expira
    else:
        db.session.add(BloqueoIP(
            ip_address=ip,
            motivo=motivo,
            desbloquear_en=expira,
        ))
    db.session.commit()


def cuenta_esta_bloqueada(usuario) -> bool:
    """
    True si la cuenta está bloqueada y el bloqueo aún está vigente.
    Si el bloqueo ya expiró, lo revierte automáticamente.
    """
    if usuario.activo:
        return False
    # Intenta desbloquear si ya pasó el tiempo
    if usuario.desbloquear_si_expirado():
        db.session.commit()
        return False
    return True


def bloquear_cuenta_temporal(usuario):
    """
    Bloqueo temporal: desactiva al usuario BLOQUEO_EMAIL_MIN minutos.
    Se desbloquea automáticamente al expirar (vía desbloquear_si_expirado).
    """
    usuario.activo          = False
    usuario.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=BLOQUEO_EMAIL_MIN)
    db.session.commit()


def verificar_y_aplicar_bloqueos(email: str, ip: str):
    """
    Llamar DESPUÉS de un intento fallido.
    Aplica bloqueo de email o IP si se superan los umbrales.
    Retorna: ('email', usuario) | ('ip', None) | (None, None)
    """
    from models.usuario import Usuario

    # Bloqueo de cuenta si supera MAX_INTENTOS_EMAIL
    intentos_email = contar_intentos_fallidos_email(email)
    if intentos_email >= MAX_INTENTOS_EMAIL:
        usuario = Usuario.query.filter_by(email=email.lower()).first()
        if usuario and usuario.activo:
            bloquear_cuenta_temporal(usuario)
            return 'email', usuario

    # Bloqueo de IP si supera MAX_INTENTOS_IP
    intentos_ip = contar_intentos_fallidos_ip(ip)
    if intentos_ip >= MAX_INTENTOS_IP:
        bloquear_ip(ip, motivo=f'Más de {MAX_INTENTOS_IP} intentos fallidos')
        return 'ip', None

    return None, None


# ─── Tokens de sesión seguros ─────────────────────────────────────────────────

def crear_token_sesion(usuario_id: int, ip: str) -> str:
    """Crea y persiste un token único de sesión. Retorna el token."""
    from models.seguridad import SesionActiva
    token = secrets.token_hex(32)          # 64 caracteres aleatorios
    sesion = SesionActiva(
        usuario_id=usuario_id,
        token=token,
        ip_address=ip,
        user_agent=request.headers.get('User-Agent', '')[:255],
        expira_en=datetime.utcnow() + timedelta(hours=EXPIRACION_SESION_H),
    )
    db.session.add(sesion)
    db.session.commit()
    return token


def validar_token_sesion(token: str) -> bool:
    """True si el token existe, está activo y no ha expirado."""
    from models.seguridad import SesionActiva
    if not token:
        return False
    sesion = SesionActiva.query.filter_by(token=token, activa=True).first()
    if not sesion:
        return False
    if not sesion.esta_vigente:
        sesion.activa = False
        db.session.commit()
        return False
    return True


def invalidar_token_sesion(token: str):
    """Desactiva el token (logout)."""
    from models.seguridad import SesionActiva
    sesion = SesionActiva.query.filter_by(token=token).first()
    if sesion:
        sesion.activa = False
        db.session.commit()


def invalidar_todas_sesiones(usuario_id: int):
    """Cierra todas las sesiones activas de un usuario."""
    from models.seguridad import SesionActiva
    SesionActiva.query.filter_by(usuario_id=usuario_id, activa=True).update({'activa': False})
    db.session.commit()


# ─── Doble factor (2FA) ───────────────────────────────────────────────────────

def _generar_codigo_otp() -> str:
    """Genera un código numérico de 6 dígitos."""
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def crear_codigo_2fa(usuario_id: int) -> str:
    """Crea (o remplaza) el código 2FA activo para el usuario. Retorna el código."""
    from models.seguridad import Codigo2FA
    # Invalidar códigos anteriores
    Codigo2FA.query.filter_by(usuario_id=usuario_id, usado=False).update({'usado': True})
    db.session.commit()

    codigo = _generar_codigo_otp()
    registro = Codigo2FA(
        usuario_id=usuario_id,
        codigo=codigo,
        expira_en=datetime.utcnow() + timedelta(minutes=EXPIRACION_2FA_MIN),
    )
    db.session.add(registro)
    db.session.commit()
    return codigo


def verificar_codigo_2fa(usuario_id: int, codigo_ingresado: str) -> bool:
    """True si el código es correcto y no ha expirado. Lo marca como usado."""
    from models.seguridad import Codigo2FA
    registro = Codigo2FA.query.filter_by(
        usuario_id=usuario_id,
        codigo=codigo_ingresado.strip(),
        usado=False,
    ).first()
    if not registro or not registro.es_valido:
        return False
    registro.usado = True
    db.session.commit()
    return True


def enviar_codigo_2fa(usuario, codigo: str):
    """Envía el código OTP al email del usuario."""
    try:
        msg = Message(
            subject='🔐 Tu código de verificación — Anita New Style',
            recipients=[usuario.email],
            html=f"""
            <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                        background:#fff;border-radius:12px;padding:32px;
                        border:1px solid #eee;">
              <h2 style="color:#b5469a;text-align:center;">ANITA NEW STYLE</h2>
              <p>Hola <strong>{usuario.nombre}</strong>,</p>
              <p>Tu código de verificación es:</p>
              <div style="font-size:42px;font-weight:bold;letter-spacing:12px;
                          text-align:center;color:#b5469a;padding:16px 0;">
                {codigo}
              </div>
              <p style="color:#888;font-size:13px;">
                Este código expira en <strong>{EXPIRACION_2FA_MIN} minutos</strong>.<br>
                Si no fuiste tú, ignora este mensaje.
              </p>
            </div>
            """,
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f'[2FA] Error enviando email: {e}')
        return False


# ─── Rate-limiting para verificación 2FA ─────────────────────────────────────

def contar_intentos_2fa_fallidos(usuario_id: int) -> int:
    """
    Cuenta intentos fallidos de 2FA en la ventana activa.
    Usa la tabla IntentoLogin con motivo='2fa_incorrecto' y el campo usuario_id.
    """
    from models.seguridad import IntentoLogin
    return IntentoLogin.query.filter(
        IntentoLogin.usuario_id == usuario_id,
        IntentoLogin.exitoso == False,
        IntentoLogin.motivo_fallo == '2fa_incorrecto',
        IntentoLogin.fecha >= _ventana_inicio(),
    ).count()


def registrar_intento_2fa(usuario_id: int, exitoso: bool):
    """Registra un intento de verificación 2FA."""
    from models.seguridad import IntentoLogin
    from models.usuario import Usuario
    ip = obtener_ip()
    usuario = Usuario.query.get(usuario_id)
    email_usuario = usuario.email if usuario else ''
    intento = IntentoLogin(
        email=email_usuario,
        usuario_id=usuario_id,
        ip_address=ip,
        exitoso=exitoso,
        motivo_fallo=None if exitoso else '2fa_incorrecto',
        user_agent=request.headers.get('User-Agent', '')[:255],
    )
    db.session.add(intento)
    db.session.commit()


def sesion_2fa_bloqueada(usuario_id: int) -> bool:
    """True si el usuario superó MAX_INTENTOS_2FA intentos fallidos de código."""
    return contar_intentos_2fa_fallidos(usuario_id) >= MAX_INTENTOS_2FA
