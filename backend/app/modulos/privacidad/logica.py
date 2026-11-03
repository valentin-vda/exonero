"""Reglas de consentimiento, acceso y supresion de datos."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

from app import correo, seguridad
from app.config import ajustes
from app.enums import EstadoCuenta, EstadoFicha
from app.errores import ErrorAPI
from app.modulos.cuentas.modelos import Usuario
from app.modulos.privacidad.modelos import AuditoriaPrivacidad, Consentimiento, InvitacionParental
from app.modulos.privacidad.textos import AVISO_MENORES, AVISO_PRIVACIDAD, HASH_AVISO, VERSION_AVISO
from app.modulos.resenas.modelos import Resena
from app.modulos.resenas import logica as resenas


def ahora() -> datetime:
    return datetime.now(timezone.utc)


def auditar(db: Session, usuario_id: int | None, evento: str, detalle: str | None = None) -> None:
    db.add(AuditoriaPrivacidad(usuario_id=usuario_id, evento=evento, detalle=detalle))


def registrar_consentimiento(
    db: Session,
    usuario_id: int,
    tipo: str,
    aceptado_por: str,
    ip: str | None = None,
    agente: str | None = None,
    adulto_nombre: str | None = None,
    adulto_correo: str | None = None,
    adulto_vinculo: str | None = None,
) -> None:
    db.add(Consentimiento(
        usuario_id=usuario_id,
        tipo=tipo,
        version_documento=VERSION_AVISO,
        hash_documento=HASH_AVISO,
        aceptado_el=ahora(),
        aceptado_por=aceptado_por,
        adulto_nombre=adulto_nombre,
        adulto_correo=adulto_correo,
        adulto_vinculo=adulto_vinculo,
        ip=(ip or "")[:80] or None,
        agente_usuario=(agente or "")[:300] or None,
    ))
    auditar(db, usuario_id, "consentimiento_otorgado", tipo)


def crear_invitacion_parental(db: Session, usuario: Usuario, correo_adulto: str) -> None:
    token = secrets.token_urlsafe(32)
    instante = ahora()
    invitacion = InvitacionParental(
        usuario_id=usuario.id,
        correo_adulto=correo_adulto.lower(),
        token_hash=_hash_token(token),
        expira_el=instante + timedelta(hours=72),
        enviado_el=instante,
    )
    db.add(invitacion)
    db.flush()
    enlace = f"{ajustes.URL_FRONTEND}/consentimiento-parental#token={token}"
    correo.enviar(
        correo_adulto,
        "Autoriza la cuenta de un menor en Exonero",
        f"{AVISO_MENORES}\n\nPara autorizar o rechazar la cuenta, abri este enlace:\n{enlace}\n\n"
        "El enlace vence en 72 horas y solo puede usarse una vez.",
    )
    auditar(db, usuario.id, "invitacion_parental_enviada")


def confirmar_parental(db: Session, datos, ip: str | None, agente: str | None) -> Usuario:
    invitacion = db.scalar(select(InvitacionParental).where(
        InvitacionParental.token_hash == _hash_token(datos.token)
    ))
    if invitacion is None or invitacion.usada_el is not None or invitacion.expira_el < ahora():
        raise ErrorAPI(409, "enlace_parental_invalido")
    usuario = db.get(Usuario, invitacion.usuario_id)
    if usuario is None or usuario.estado != EstadoCuenta.pendiente_consentimiento_parental:
        raise ErrorAPI(409, "enlace_parental_invalido")

    invitacion.usada_el = ahora()
    usuario.estado = EstadoCuenta.activa
    registrar_consentimiento(
        db, usuario.id, "parental", "adulto_responsable", ip, agente,
        datos.nombre_adulto.strip(), invitacion.correo_adulto, datos.vinculo,
    )
    auditar(db, usuario.id, "cuenta_activada_por_adulto")
    return usuario


def exportar_datos(db: Session, usuario: Usuario) -> dict:
    """Exportacion inmediata y legible; nunca incluye hashes ni secretos."""
    def filas(consulta: str) -> list[dict]:
        return [dict(f) for f in db.execute(text(consulta), {"uid": usuario.id}).mappings()]

    datos = {
        "generado_el": ahora(),
        "aviso_privacidad": {"version": VERSION_AVISO, "hash": HASH_AVISO},
        "cuenta": {
            "id": usuario.id, "correo": usuario.correo, "nombre": usuario.nombre,
            "apellido": usuario.apellido, "documento": usuario.documento,
            "telefono": usuario.telefono, "fecha_nacimiento": usuario.fecha_nacimiento,
            "rol": usuario.rol.value, "estado": usuario.estado.value,
            "creado_el": usuario.creado_el,
        },
        "perfil_estudiante": filas("SELECT etapa_id,nivel,centro_id,barrio_id,direccion,adulto_nombre,adulto_telefono FROM perfil_estudiante WHERE usuario_id=:uid"),
        "perfil_profesor": filas("SELECT titular,biografia,titulo_habilitante,anios_experiencia,barrio_id,direccion_espacio,modalidad,estado_ficha,puntaje_promedio,cantidad_resenas FROM perfil_profesor WHERE usuario_id=:uid"),
        "clases": filas("SELECT id,materia_id,etapa_id,tema,inicio,fin,modalidad,ubicacion,estado,motivo,total FROM clase WHERE estudiante_id=:uid OR profesor_id=:uid ORDER BY inicio"),
        "mensajes": filas("SELECT id,hilo_id,contenido,enviado_el,leido_el FROM mensaje WHERE autor_id=:uid ORDER BY enviado_el"),
        "resenas_escritas": filas("SELECT destinatario_id,puntaje,texto,creado_el FROM resena WHERE autor_id=:uid"),
        "resenas_recibidas": filas("SELECT puntaje,texto,creado_el FROM resena WHERE destinatario_id=:uid"),
        "tarjetas_demo": filas("SELECT marca,ultimos4,titular,vence,activa FROM (SELECT CASE WHEN numero LIKE '4%' THEN 'Visa' WHEN numero LIKE '5%' THEN 'Mastercard' ELSE 'Otra' END marca, RIGHT(numero,4) ultimos4,titular,LPAD(vence_mes::text,2,'0')||'/'||RIGHT(vence_anio::text,2) vence,activa,usuario_id FROM tarjeta) t WHERE usuario_id=:uid"),
        "consentimientos": filas("SELECT tipo,version_documento,hash_documento,aceptado_el,aceptado_por,revocado_el FROM consentimiento WHERE usuario_id=:uid"),
    }
    auditar(db, usuario.id, "datos_exportados")
    return datos


def anonimizar(db: Session, usuario: Usuario, clave: str) -> None:
    if not seguridad.verificar_clave(clave, usuario.hash_clave):
        raise ErrorAPI(403, "clave_actual_incorrecta")

    # Las resenas que escribio se eliminan por decision de su propio autor.
    destinatarios = list(db.scalars(select(Resena.destinatario_id).where(Resena.autor_id == usuario.id)))
    db.execute(delete(Resena).where((Resena.autor_id == usuario.id) | (Resena.destinatario_id == usuario.id)))
    db.flush()
    for destinatario_id in set(destinatarios):
        if destinatario_id != usuario.id:
            resenas.recalcular(db, destinatario_id)

    db.execute(text("UPDATE mensaje SET contenido='[contenido eliminado]' WHERE autor_id=:uid"), {"uid": usuario.id})
    db.execute(text("UPDATE clase SET tema=NULL, ubicacion=NULL, motivo=NULL WHERE estudiante_id=:uid OR profesor_id=:uid"), {"uid": usuario.id})
    db.execute(text("UPDATE perfil_estudiante SET etapa_id=NULL,nivel=NULL,centro_id=NULL,barrio_id=NULL,direccion=NULL,latitud=NULL,longitud=NULL,adulto_nombre=NULL,adulto_telefono=NULL WHERE usuario_id=:uid"), {"uid": usuario.id})
    db.execute(text("UPDATE perfil_profesor SET titular=NULL,biografia=NULL,titulo_habilitante=NULL,barrio_id=NULL,direccion_espacio=NULL,latitud=NULL,longitud=NULL,estado_ficha=:pausada WHERE usuario_id=:uid"), {"uid": usuario.id, "pausada": EstadoFicha.pausada.value})
    db.execute(text("DELETE FROM foto_lugar WHERE perfil_profesor_id IN (SELECT id FROM perfil_profesor WHERE usuario_id=:uid)"), {"uid": usuario.id})
    db.execute(text("UPDATE tarjeta SET numero='DEMO-ELIMINADA',ccv='',titular='ELIMINADO',activa=false WHERE usuario_id=:uid"), {"uid": usuario.id})
    db.execute(text("UPDATE cuenta_cobro SET identificador='eliminada-'||id::text,titular=CASE WHEN tipo='banco' THEN 'ELIMINADO' ELSE NULL END,activa=false,es_principal=false WHERE usuario_id=:uid"), {"uid": usuario.id})
    db.execute(text("UPDATE consentimiento SET adulto_nombre=NULL,adulto_correo=NULL,adulto_vinculo=NULL,ip=NULL,agente_usuario=NULL WHERE usuario_id=:uid"), {"uid": usuario.id})

    usuario.correo = f"eliminado-{usuario.id}-{secrets.token_hex(6)}@anonimo.invalid"
    usuario.hash_clave = seguridad.hashear_clave(secrets.token_urlsafe(32))
    usuario.nombre = "Usuario"
    usuario.apellido = "eliminado"
    usuario.documento = None
    usuario.telefono = None
    usuario.fecha_nacimiento = None
    usuario.foto_base64 = None
    usuario.estado = EstadoCuenta.anonimizada
    usuario.anonimizado_el = ahora()
    usuario.version_sesion += 1
    auditar(db, usuario.id, "cuenta_anonimizada")


def borrar_resena_propia(db: Session, autor_id: int, destinatario_id: int) -> None:
    resena = db.scalar(select(Resena).where(
        Resena.autor_id == autor_id, Resena.destinatario_id == destinatario_id
    ))
    if resena is None:
        raise ErrorAPI(404, "resena_no_existe")
    db.delete(resena)
    db.flush()
    resenas.recalcular(db, destinatario_id)
    auditar(db, autor_id, "resena_propia_eliminada", str(destinatario_id))


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
