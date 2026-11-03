"""Purgas de conservacion. Ejecutar: python -m app.privacidad_mantenimiento"""

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, text

from app.db import SesionLocal
from app.enums import EstadoCuenta
from app.modulos.cuentas.modelos import Usuario
from app.modulos.privacidad.modelos import AuditoriaPrivacidad, InvitacionParental


def ejecutar() -> dict[str, int]:
    ahora = datetime.now(timezone.utc)
    with SesionLocal() as db:
        invitaciones = db.execute(delete(InvitacionParental).where(
            InvitacionParental.expira_el < ahora - timedelta(days=1)
        )).rowcount
        auditoria = db.execute(delete(AuditoriaPrivacidad).where(
            AuditoriaPrivacidad.creado_el < ahora - timedelta(days=180)
        )).rowcount
        pendientes = list(db.scalars(select(Usuario).where(
            Usuario.estado == EstadoCuenta.pendiente_consentimiento_parental,
            Usuario.creado_el < ahora - timedelta(days=7),
        )))
        # Nunca tuvieron una cuenta activa: CASCADE retira perfil, invitacion y
        # consentimientos asociados sin afectar historiales de terceros.
        for usuario in pendientes:
            db.delete(usuario)
        mensajes = db.execute(text(
            "UPDATE mensaje SET contenido='[contenido vencido]' "
            "WHERE enviado_el < :limite AND contenido NOT LIKE '[contenido %]'"
        ), {"limite": ahora - timedelta(days=730)}).rowcount
        clases = db.execute(text(
            "UPDATE clase SET tema=NULL, ubicacion=NULL, motivo=NULL "
            "WHERE fin < :limite AND (tema IS NOT NULL OR ubicacion IS NOT NULL OR motivo IS NOT NULL)"
        ), {"limite": ahora - timedelta(days=730)}).rowcount
        db.commit()
        return {
            "invitaciones": invitaciones,
            "auditoria": auditoria,
            "cuentas_pendientes": len(pendientes),
            "mensajes_minimizados": mensajes,
            "clases_minimizadas": clases,
        }


if __name__ == "__main__":
    print(ejecutar())
