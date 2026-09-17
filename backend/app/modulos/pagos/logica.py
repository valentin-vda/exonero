"""Funciones publicas del modulo pagos - dueno P4.

El cobro es SIMULADO de punta a punta. No hay pasarela: los datos de la tarjeta
se guardan en la base y el cobro es un registro que cambia de estado. Siempre
responde bien, salvo que se fuerce el error a proposito para probar 1g.

Quien consume que:
  - clases -> retener() al crear, cobrar() al aprobar, liberar() al rechazar,
              reembolsar() al cancelar

Las cuatro funciones son las cuatro transiciones del estado de un cobro, y son
la unica forma de escribir en esa tabla.
"""

from decimal import Decimal

from sqlalchemy.orm import Session


def retener(db: Session, clase_id: int, tarjeta_id: int, importe: Decimal) -> object:
    """Crea el cobro en estado retenido. Lo llama clases al crear la clase.

    Retenido quiere decir: el alumno ya puso la tarjeta, pero el profesor
    todavia no acepto. Si rechaza, se libera y no se cobro nada.

    TODO (P4): implementar.
      1. Validar que la tarjeta exista, este activa y sea del alumno.
      2. Validar que no este vencida -> 402 "tarjeta_vencida".
      3. Insertar el cobro con estado retenido e importe = total de la clase.
      4. Aca va el gancho para forzar el error y poder probar 1g: por ejemplo,
         si el numero termina en 0000, devolver 402 "cobro_rechazado".
      Sin commit: lo hace clases, que esta orquestando la transaccion entera.
    """
    raise NotImplementedError("P4 - pagos: retener el importe")


def cobrar(db: Session, clase_id: int) -> object:
    """Pasa el cobro de retenido a cobrado. Lo llama clases al aprobar.

    A partir de aca el importe cuenta en los ingresos del profesor.

    TODO (P4): implementar. estado = cobrado, cobrado_el = now().
    409 si no estaba retenido.
    """
    raise NotImplementedError("P4 - pagos: cobrar")


def liberar(db: Session, clase_id: int) -> object:
    """Pasa el cobro de retenido a liberado. Lo llama clases al RECHAZAR.

    Importante: se llama ANTES de borrar la clase. La clase rechazada
    desaparece, pero el cobro liberado queda como registro de que hubo un
    movimiento. Por eso el cobro no puede vivir adentro de la clase.

    TODO (P4): implementar. estado = liberado, liberado_el = now().
    """
    raise NotImplementedError("P4 - pagos: liberar")


def reembolsar(clase_id: int) -> None:
    """Devuelve el importe al alumno. Corre como BackgroundTask al cancelar.

    OJO: esta funcion NO recibe la sesion de la request. Corre despues de que
    la respuesta ya se envio, y para entonces esa sesion esta cerrada. Tiene
    que abrir la suya propia con SesionLocal() y cerrarla al terminar.

    TODO (P4): implementar.
      1. Abrir sesion propia.
      2. Buscar el cobro de esa clase. Si ya esta reembolsado, no hacer nada
         (la funcion tiene que ser idempotente: si se encola dos veces, no
         puede devolver la plata dos veces).
      3. estado = reembolsado, reembolsado_el = now().
      4. Descontar esa clase de lo que se le liquida al profesor: como los
         ingresos son una suma sobre los cobrados, alcanza con que deje de
         estar en ese estado.
      5. Cerrar la sesion, siempre, incluso si algo falla.

    PENDIENTE DE DECIDIR: la politica de cancelacion. Si se reembolsa el total
    siempre o si hay un plazo minimo. Hoy asume total.
    """
    raise NotImplementedError("P4 - pagos: reembolsar")


def ingresos_de(db: Session, profesor_usuario_id: int, periodo: str) -> dict:
    """Los ingresos del profesor. Compartido por el panel 1d y el perfil 1j.

    Todo sale de cobro, no hay tabla de liquidaciones:
      cobrado   sum(importe) de sus cobros en estado cobrado
      pendiente sum(importe) de los retenidos, o sea lo que espera aprobacion
      promedio  cobrado dividido la cantidad de clases dictadas

    TODO (P4): implementar. El join va por clase.profesor_id.
    """
    raise NotImplementedError("P4 - pagos: ingresos del profesor")


def marca_de(numero: str) -> str:
    """Deduce la marca a partir del numero. Util, no critico.

    4 -> Visa, 5 -> Mastercard, el resto -> Otra.

    TODO (P4): implementar.
    """
    raise NotImplementedError("P4 - pagos: deducir la marca de la tarjeta")
