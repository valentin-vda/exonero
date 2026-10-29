"""Contratos de entrada y salida del modulo pagos."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TarjetaIn(BaseModel):
    """POST /pagos/tarjetas - 1e y 1g."""

    numero: str = Field(min_length=13, max_length=19)
    titular: str
    vence_mes: int = Field(ge=1, le=12)
    vence_anio: int
    ccv: str = Field(min_length=3, max_length=4)


class TarjetaOut(BaseModel):
    """Lo que se devuelve de una tarjeta.

    NUNCA el numero completo ni el CCV, aunque esten guardados. La marca se
    deduce del primer digito y ultimos4 son los ultimos cuatro: con eso alcanza
    para que el alumno reconozca cual es.
    """

    id: int
    marca: str        # Visa, Mastercard, OCA, Otra
    ultimos4: str
    titular: str
    vence: str        # MM/AA


class CuentaCobroIn(BaseModel):
    """POST /pagos/cuentas - 1j, la tarjeta "Cobros".

    Lo que se manda depende del tipo:
      banco         banco (el codigo: "brou", "itau"...), identificador (el
                    numero; se aceptan espacios y guiones), moneda y titular
      mercado_pago  identificador (el correo). banco, moneda y titular se
                    ignoran: Mercado Pago no los usa.

    Literal en tipo y moneda: un valor que no esta en la lista es un 422 de
    FastAPI, como TemaIn. El resto (que el numero sean digitos, que el banco
    exista, que el correo sea valido) lo valida pagos/logica.py con sus
    codigos propios, para que el frontend pueda decir que esta mal.
    """

    tipo: Literal["banco", "mercado_pago"]
    banco: str | None = None
    # Los topes son solo de seguridad (que no manden un texto enorme): los
    # limites reales del numero, entre 6 y 20 digitos, los mira la logica.
    identificador: str = Field(min_length=1, max_length=254)
    titular: str | None = Field(default=None, max_length=120)
    moneda: Literal["UYU", "USD"] | None = None


class CuentaCobroOut(BaseModel):
    """Lo que se devuelve de una cuenta de cobro.

    NUNCA el numero de cuenta completo, aunque este guardado: `visible` es
    "•••• 3391" para un banco. El correo de Mercado Pago si va entero (como en
    el mockup): es el dato con el que el profesor reconoce la cuenta, y no
    sirve para sacar plata.
    """

    id: int
    tipo: str                 # banco | mercado_pago
    banco: str | None = None  # el codigo: "itau"
    banco_nombre: str | None = None  # el nombre que se muestra: "Itaú"
    visible: str              # "•••• 3391" o "lucia.fernandez@example.com"
    titular: str | None = None
    moneda: str | None = None  # UYU | USD, solo en banco
    es_principal: bool


class MovimientoOut(BaseModel):
    """Una fila del historial de pagos de 1e. Incluye los reembolsos.

    fecha es la del ULTIMO movimiento del cobro (reembolsado, liberado, cobrado
    o retenido, el que haya pasado ultimo): es lo que le importa al alumno.

    clase_id, materia y contraparte vienen en null cuando el profesor RECHAZO
    la solicitud: la clase se borro y el cobro liberado quedo solo. El
    frontend lo muestra como "Solicitud rechazada".
    """

    id: int
    fecha: datetime
    clase_id: int | None = None
    materia: str | None = None
    contraparte: str | None = None
    importe: Decimal
    estado: str


class PuntoIngreso(BaseModel):
    """Un tramo del grafico de ingresos: etiqueta = "AAAA-MM-DD" (inicio del tramo)."""

    etiqueta: str
    importe: Decimal


class IngresosOut(BaseModel):
    """GET /pagos/ingresos - compartido por 1d y 1j.

    cobrado    suma de los cobros en estado cobrado
    pendiente  lo retenido, todavia sin aprobar
    """

    cobrado: Decimal
    pendiente: Decimal
    promedio_por_clase: Decimal
    serie: list[PuntoIngreso] = []


class OkOut(BaseModel):
    ok: bool = True
