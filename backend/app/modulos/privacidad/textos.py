"""Textos legales versionados del prototipo.

No sustituyen la revision de un profesional ni la identificacion del
responsable. El hash permite demostrar exactamente que texto fue aceptado.
"""

from hashlib import sha256

VERSION_AVISO = "2026-11-03"

AVISO_PRIVACIDAD = """Exonero es un prototipo academico. No ingreses datos reales.
Usamos los datos para crear y proteger tu cuenta, conectar estudiantes con
profesores, coordinar clases, mensajes, resenas y pagos ficticios. No pedimos
datos sensibles. Podes acceder, corregir y cancelar tus datos desde Privacidad.
Los datos no se usan para fines incompatibles ni se ceden fuera de los
prestadores necesarios para operar el servicio. El responsable legal y la
inscripcion ante la URCDP estan pendientes; por eso este prototipo no esta
habilitado para produccion."""

AVISO_MENORES = """Si sos menor, un adulto responsable debe autorizar el uso de
tus datos antes de que puedas entrar. El adulto recibira un enlace, conocera
para que se usan los datos y podra aceptar o rechazar. No compartas datos de
salud, religion, origen, vida privada ni informacion que no sea necesaria para
coordinar tus clases."""

HASH_AVISO = sha256(AVISO_PRIVACIDAD.encode("utf-8")).hexdigest()
