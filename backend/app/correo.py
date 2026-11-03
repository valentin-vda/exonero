"""Entrega de correo simple; Mailpit lo captura durante el desarrollo."""

import smtplib
from email.message import EmailMessage

from app.config import ajustes
from app.errores import ErrorAPI


def enviar(destino: str, asunto: str, texto: str) -> None:
    mensaje = EmailMessage()
    mensaje["From"] = ajustes.SMTP_REMITENTE
    mensaje["To"] = destino
    mensaje["Subject"] = asunto
    mensaje.set_content(texto)
    try:
        with smtplib.SMTP(ajustes.SMTP_HOST, ajustes.SMTP_PUERTO, timeout=5) as smtp:
            smtp.send_message(mensaje)
    except (OSError, smtplib.SMTPException) as exc:
        raise ErrorAPI(503, "correo_no_disponible") from exc
