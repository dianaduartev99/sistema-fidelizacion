import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)


async def enviar_comprobante_uso_puntos(
    email_destino: str,
    nombre_cliente: str,
    puntos_utilizados: int,
    concepto: str,
    fecha: str,
    id_transaccion: int,
) -> bool:
    """Envía un correo de comprobante al cliente cuando utiliza puntos."""
    if not SMTP_USER or not SMTP_PASSWORD:
        print("[EMAIL] Credenciales SMTP no configuradas. Omitiendo envío.")
        return False

    mensaje = MIMEMultipart("alternative")
    mensaje["Subject"] = f"Comprobante de uso de puntos - Transacción #{id_transaccion}"
    mensaje["From"] = EMAIL_FROM
    mensaje["To"] = email_destino

    cuerpo_html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #2c7be5;">Sistema de Fidelización</h2>
        <p>Estimado/a <strong>{nombre_cliente}</strong>,</p>
        <p>Te confirmamos el siguiente uso de puntos:</p>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
            <tr><td><strong>ID Transacción</strong></td><td>#{id_transaccion}</td></tr>
            <tr><td><strong>Concepto</strong></td><td>{concepto}</td></tr>
            <tr><td><strong>Puntos utilizados</strong></td><td>{puntos_utilizados}</td></tr>
            <tr><td><strong>Fecha</strong></td><td>{fecha}</td></tr>
        </table>
        <p>¡Gracias por tu preferencia!</p>
    </body>
    </html>
    """

    mensaje.attach(MIMEText(cuerpo_html, "html"))

    try:
        await aiosmtplib.send(
            mensaje,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_USER,
            password=SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"[EMAIL] Error al enviar correo: {e}")
        return False
