"""Funciones publicas del modulo clases - dueno P4.

clases es el modulo mas pesado y el de mayor riesgo: maneja estados y plata.

Quien consume que:
  - agenda -> clases_aprobadas_entre(), para descontar lo ocupado de los huecos
  - agenda -> clases_entre(), para el calendario semanal de 1i
  - resenas -> tuvieron_clase(), para exigir que solo resene quien tuvo clase

A quien le pide datos:
  - perfiles  -> precio_vigente()
  - catalogos -> parametros_vigentes()
  - agenda    -> verificar()
  - pagos     -> retener(), cobrar(), liberar(), reembolsar()
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session


def cotizar(db: Session, profesor_usuario_id: int, duracion_min: int, modalidad: str, con_traslado: bool) -> dict:
    """El calculo del importe. LA FUNCION MAS PELIGROSA DE DUPLICAR.

    El estimado de 1f y el detalle de 1g salen de aca. Si alguien la reescribe
    en otro lado, los dos numeros van a diferir y nadie va a saber cual vale.

    Orden del calculo:
      horas     = duracion_min / 60
      subtotal  = precio_hora * horas
      traslado  = costo_traslado del profesor, solo si con_traslado
      comision  = (subtotal + traslado) * pct_comision / 100
      impuesto  = (subtotal + traslado + comision) * pct_iva / 100
      total     = subtotal + traslado + comision + impuesto

    TODO (P4): implementar.
      1. precio = perfiles.logica.precio_vigente(db, profesor_id, modalidad)
         Si no tiene precio para esa modalidad -> 400 "sin_precio".
      2. params = catalogos.logica.parametros_vigentes(db)
      3. Hacer las cuentas con Decimal, NUNCA con float: con float, 1913.18
         puede salir 1913.1800000000003 y el comprobante no cuadra.
      4. Redondear a dos decimales al final de cada paso, con ROUND_HALF_UP.
    """
    raise NotImplementedError("P4 - clases: cotizar")


def crear(db: Session, estudiante_id: int, datos) -> object:
    """Crea la clase en pendiente, con los precios congelados y el cobro retenido.

    Es el confirmar de 1g, y toca tres modulos. Va todo en UNA transaccion: si
    el cobro falla, la clase no tiene que quedar creada.

    TODO (P4): implementar.
      1. agenda.logica.verificar() otra vez -> 409 "horario_ocupado" si no.
         Se revalida aunque el checkout ya lo haya chequeado: entre que abrio
         la pantalla y confirmo, el hueco se pudo ocupar.
      2. cotizar() para tener el desglose.
      3. Insertar la clase con estado pendiente, fin = inicio + duracion, y
         TODOS los importes copiados (precio_hora, pct_comision, pct_iva,
         subtotal, impuesto, total).
      4. pagos.logica.retener(db, clase.id, tarjeta_id, total)
         -> 402 "cobro_rechazado" si el mock devuelve error.
      5. commit.
    """
    raise NotImplementedError("P4 - clases: crear la clase")


def aprobar(db: Session, clase_id: int, profesor_id: int) -> object:
    """El profesor acepta. La clase pasa a aprobada y el cobro a cobrado.

    TODO (P4): implementar.
      1. 403 si la clase no es de este profesor; 409 si no esta pendiente.
      2. Pasar a aprobada. La restriccion EXCLUDE de la base puede rechazar el
         UPDATE si mientras tanto se aprobo otra encima: capturar el
         IntegrityError y devolver 409 "horario_ocupado".
      3. pagos.logica.cobrar(db, clase_id).
    """
    raise NotImplementedError("P4 - clases: aprobar")


def rechazar(db: Session, clase_id: int, profesor_id: int) -> None:
    """El profesor rechaza. SE BORRA LA FILA y se libera el cobro.

    La clase rechazada no deja rastro: no es un estado, es una fila que no
    existe mas. El cobro SI queda, con estado liberado, porque hubo un
    movimiento de plata que registrar.

    TODO (P4): implementar.
      1. 403 si no es de este profesor; 409 si no esta pendiente.
      2. pagos.logica.liberar(db, clase_id) ANTES de borrar la clase.
      3. Borrar la fila.
    """
    raise NotImplementedError("P4 - clases: rechazar")


def cancelar(db: Session, clase_id: int, quien_id: int, motivo: str | None, tareas) -> object:
    """Cualquiera de las dos partes cancela. NO se borra: cambia de estado.

    Queda en el historial porque el reembolso y la tasa de cancelacion de 1d
    la necesitan.

    TODO (P4): implementar.
      1. 403 si quien cancela no es parte de la clase.
      2. 409 si ya esta cancelada o dictada.
      3. estado = cancelada, cancelada_por = estudiante o profesor segun el rol
         del token, motivo = el que vino.
      4. Encolar el reembolso: tareas.add_task(pagos.logica.reembolsar, clase_id).
         Corre como BackgroundTask para que el cancelar responda al instante.

    PENDIENTE DE DECIDIR (lo marca la spec): la politica de cancelacion. Si se
    reembolsa el total siempre, o si hay un plazo minimo. Hoy asume total.
    """
    raise NotImplementedError("P4 - clases: cancelar")


def reprogramar(db: Session, clase_id: int, quien_id: int, inicio_nuevo: datetime) -> object:
    """Cambia la fecha y VUELVE A PENDIENTE, para que el profesor apruebe de nuevo.

    TODO (P4): implementar.
      1. 403 si no es parte de la clase.
      2. agenda.logica.verificar() en el horario nuevo -> 409 si esta ocupado.
      3. Cambiar inicio y fin, estado = pendiente.
      4. Los importes NO se recalculan: siguen congelados. Es la misma clase
         movida de lugar, no una nueva.
    """
    raise NotImplementedError("P4 - clases: reprogramar")


def completar(db: Session, clase_id: int, profesor_id: int, estado: str) -> object:
    """El profesor la marca como dictada o no_asistida.

    TODO (P4): implementar.
      1. 403 si no es de este profesor; 409 si no esta aprobada.
      2. Si es dictada, incrementar clases_dictadas del perfil del profesor.
      3. Habilita resenar: resenas.tuvieron_clase() empieza a devolver True.
    """
    raise NotImplementedError("P4 - clases: marcar dictada")


# --- Lo que consumen los otros modulos --------------------------------------

def clases_aprobadas_entre(db: Session, profesor_id: int, desde: datetime, hasta: datetime) -> list[dict]:
    """Las clases aprobadas de un profesor en un rango. Las descuenta agenda.

    Solo aprobadas: las pendientes no ocupan el hueco.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: clases aprobadas en un rango")


def clases_entre(db: Session, usuario_id: int, desde: datetime, hasta: datetime, estado=None) -> list[dict]:
    """Las clases de un usuario en un rango, sea alumno o profesor.

    La misma consulta sirve a 1b, 1d y 1i: el rol sale del token y decide si se
    filtra por estudiante_id o por profesor_id.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: clases de un usuario en un rango")


def tuvieron_clase(db: Session, a_id: int, b_id: int) -> bool:
    """True si esas dos personas tuvieron al menos una clase dictada.

    Lo usa resenas para rechazar con 403 "sin_clases_con_esa_persona" a quien
    intente resenar a alguien con quien nunca tuvo clase.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - clases: saber si dos personas tuvieron clase")
