"""Rutas HTTP del modulo pagos - dueno P4.

Todo cuelga de /api/pagos.

Las tarjetas son el mismo recurso desde dos pantallas: el alta desde el
checkout (1g) y la administracion desde el perfil (1e). No se duplica.
"""

from datetime import date

from fastapi import APIRouter, status

from app.dependencias import Db, Yo
from app.modulos.pagos import esquemas

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.get("/tarjetas", response_model=list[esquemas.TarjetaOut])
def listar_tarjetas(yo: Yo, db: Db):
    """Las tarjetas activas del alumno. Compartido por 1e y 1g.

    No hay tarjeta principal: el alumno elige una en cada compra.

    NUNCA devuelve el numero completo ni el CCV, aunque esten guardados.

    TODO (P4): implementar. 403 si el rol no es estudiante.
    """
    raise NotImplementedError("P4 - pagos: GET /pagos/tarjetas")


@router.post("/tarjetas", response_model=esquemas.TarjetaOut, status_code=status.HTTP_201_CREATED)
def agregar_tarjeta(datos: esquemas.TarjetaIn, yo: Yo, db: Db):
    """Alta de tarjeta. Compartido por 1e y 1g.

    Se guarda tal cual, sin pasarela. Ver la advertencia de pagos/modelos.py.

    TODO (P4): implementar.
      1. Validar que el numero sea solo digitos y que no este vencida.
      2. Deducir la marca con logica.marca_de().
      3. Guardar y devolver la version segura, solo con ultimos4.
    """
    raise NotImplementedError("P4 - pagos: POST /pagos/tarjetas")


@router.delete("/tarjetas/{tarjeta_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar_tarjeta(tarjeta_id: int, yo: Yo, db: Db):
    """Da de baja una tarjeta. Compartido por 1e y 1g.

    Baja LOGICA (activa = false), no DELETE: los cobros viejos apuntan a esta
    fila y el historial de 1e tiene que poder decir con que se pago.

    TODO (P4): implementar. 403 si la tarjeta no es de este usuario.
    """
    raise NotImplementedError("P4 - pagos: DELETE /pagos/tarjetas/{id}")


@router.get("/historial", response_model=list[esquemas.MovimientoOut])
def historial(yo: Yo, db: Db, desde: date | None = None, hasta: date | None = None, pagina: int = 1):
    """El historial de pagos del alumno. 1e.

    Son las filas de cobro de sus clases, con fecha, clase, importe y estado.
    Incluye los reembolsos de las canceladas.

    TODO (P4): implementar. Join con clase para traer materia y contraparte.
    """
    raise NotImplementedError("P4 - pagos: GET /pagos/historial")


@router.get("/ingresos", response_model=esquemas.IngresosOut)
def ingresos(yo: Yo, db: Db, periodo: str = "mes", agrupar: str = "semana"):
    """Los ingresos del profesor. Compartido por 1d y 1j.

    El grafico del panel y el resumen del perfil salen del mismo endpoint.

    TODO (P4): implementar. Envolver logica.ingresos_de().
    403 si el rol no es profesor.
    """
    raise NotImplementedError("P4 - pagos: GET /pagos/ingresos")
