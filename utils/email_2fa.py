from flask import current_app, render_template_string
from flask_mail import Message
from app_extensions import mail


TEMPLATE_2FA = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #f9f4f8; margin:0; padding:20px; }
    .card { background:#fff; max-width:480px; margin:0 auto; border-radius:16px;
            box-shadow:0 4px 24px rgba(165,54,148,.12); overflow:hidden; }
    .header { background: linear-gradient(135deg,#a53694,#c45fa8); padding:32px 24px; text-align:center; }
    .brand  { color:#fff; font-size:1.6rem; font-weight:800; letter-spacing:2px; }
    .body   { padding:32px 24px; }
    .code-box {
      background: linear-gradient(135deg,#f3e6f0,#fdf0fb);
      border: 2px dashed #a53694;
      border-radius: 12px; text-align:center; padding:24px; margin:24px 0;
    }
    .code   { font-size:2.8rem; font-weight:900; letter-spacing:10px;
              color:#a53694; font-family:monospace; }
    .expira { font-size:.8rem; color:#888; margin-top:8px; }
    .aviso  { background:#fff8e1; border-left:4px solid #ffc107; border-radius:6px;
              padding:12px 16px; font-size:.82rem; color:#7a5700; margin-top:16px; }
    .footer { text-align:center; padding:16px 24px; font-size:.75rem; color:#aaa;
              border-top:1px solid #f0e8ee; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="brand">ANITA NEW STYLE</div>
      <div style="color:rgba(255,255,255,.85);font-size:.9rem;margin-top:4px;">Verificación de identidad</div>
    </div>
    <div class="body">
      <p style="color:#444;">Hola <strong>{{ nombre }}</strong>,</p>
      <p style="color:#666;font-size:.9rem;">
        Alguien inició sesión con tu cuenta. Ingresa este código para confirmar que eres tú:
      </p>
      <div class="code-box">
        <div class="code">{{ codigo }}</div>
        <div class="expira">⏱ Válido por <strong>10 minutos</strong></div>
      </div>
      <div class="aviso">
        🔒 Si no fuiste tú, ignora este correo. Tu cuenta sigue protegida.
      </div>
    </div>
    <div class="footer">
      Anita New Style · Este es un correo automático, no respondas.
    </div>
  </div>
</body>
</html>
"""

def enviar_codigo_2fa(usuario):
    """Genera y envía el código 2FA al correo del usuario."""
    from models.codigo_2fa import Codigo2FA
    registro = Codigo2FA.generar(usuario.id)   # crea el registro (sin commit aún)
    codigo   = registro.codigo
    try:
        msg = Message(
            subject='🔐 Tu código de verificación — Anita New Style',
            recipients=[usuario.email],
            html=render_template_string(TEMPLATE_2FA,
                                        nombre=usuario.nombre,
                                        codigo=codigo),
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        return True
    except Exception as e:
            current_app.logger.error(f'Error enviando 2FA a {usuario.email}: {e}')
            print(f'ERROR 2FA: {e}')   # 👈 agrega esta línea
            return False


TEMPLATE_RESET_PASSWORD = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #f9f4f8; margin:0; padding:20px; }
    .card { background:#fff; max-width:480px; margin:0 auto; border-radius:16px;
            box-shadow:0 4px 24px rgba(165,54,148,.12); overflow:hidden; }
    .header { background: linear-gradient(135deg,#a53694,#c45fa8); padding:32px 24px; text-align:center; }
    .brand  { color:#fff; font-size:1.6rem; font-weight:800; letter-spacing:2px; }
    .body   { padding:32px 24px; }
    .btn-reset {
      display:block; width:100%; padding:16px; margin:24px 0;
      background: linear-gradient(135deg,#a53694,#c45fa8);
      color:#fff; text-decoration:none; text-align:center;
      border-radius:12px; font-weight:700; font-size:1rem; letter-spacing:.5px;
    }
    .expira { font-size:.8rem; color:#888; text-align:center; margin-top:-12px; margin-bottom:16px; }
    .aviso  { background:#fff8e1; border-left:4px solid #ffc107; border-radius:6px;
              padding:12px 16px; font-size:.82rem; color:#7a5700; margin-top:16px; }
    .footer { text-align:center; padding:16px 24px; font-size:.75rem; color:#aaa;
              border-top:1px solid #f0e8ee; }
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <div class="brand">ANITA NEW STYLE</div>
      <div style="color:rgba(255,255,255,.85);font-size:.9rem;margin-top:4px;">Recuperación de contraseña</div>
    </div>
    <div class="body">
      <p style="color:#444;">Hola <strong>{{ nombre }}</strong>,</p>
      <p style="color:#666;font-size:.9rem;">
        Recibimos una solicitud para restablecer la contraseña de tu cuenta. Haz clic en el botón para crear una nueva:
      </p>
      <a href="{{ url_reset }}" class="btn-reset">🔑 Restablecer mi contraseña</a>
      <p class="expira">⏱ Este enlace es válido por <strong>30 minutos</strong></p>
      <div class="aviso">
        🔒 Si no solicitaste esto, ignora este correo. Tu contraseña no cambiará.
      </div>
    </div>
    <div class="footer">
      Anita New Style · Este es un correo automático, no respondas.
    </div>
  </div>
</body>
</html>
"""


def enviar_recuperacion_password(usuario, token):
    """Envía el correo con el enlace de recuperación de contraseña."""
    from flask import url_for
    try:
        url_reset = url_for('auth.restablecer_password', token=token, _external=True)
        msg = Message(
            subject='🔑 Recupera tu contraseña — Anita New Style',
            recipients=[usuario.email],
            html=render_template_string(TEMPLATE_RESET_PASSWORD,
                                        nombre=usuario.nombre,
                                        url_reset=url_reset),
            sender=current_app.config.get('MAIL_DEFAULT_SENDER')
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Error enviando recuperación a {usuario.email}: {e}')
        return False
