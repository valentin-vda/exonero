"""Funciones publicas del modulo catalogos · dueno P2.

Esto es lo que pueden llamar los otros modulos. Todo lo demas de catalogos es
privado. La otra puerta de entrada es rutas.py, que usa el frontend.

Quien consume que:
  - clases  -> parametros_vigentes(), para congelar comision e IVA en la clase
  - busqueda -> centroide_barrio(), para ordenar por cercania
"""

from decimal import Decimal

from sqlalchemy.orm import Session


def parametros_vigentes(db: Session) -> dict[str, Decimal]:
    """Devuelve la comision de servicio y la tasa de IVA vigentes hoy.

    Formato: {"comision_servicio": Decimal("10.00"), "tasa_iva": Decimal("22.00")}

    Es lo que POST /clases/cotizar y POST /clases usan para armar el desglose.
    Los porcentajes se guardan congelados en la clase: si manana cambia la
    comision, las clases ya creadas siguen valiendo lo mismo.

    TODO (P2): implementar.
      1. Por cada clave ('comision_servicio', 'tasa_iva') buscar la fila con
         el vigente_desde mas grande que sea <= hoy.
      2. Armar el diccionario. Si falta alguna clave, levantar un error claro:
         sin estos valores no se puede cotizar nada.
    """
    raise NotImplementedError("P2 · catalogos: leer los parametros vigentes")


def centroide_barrio(db: Session, barrio_id: int) -> tuple[Decimal, Decimal] | None:
    """Devuelve (latitud, longitud) del centroide de un barrio, o None.

    Lo usa busqueda para calcular distancias aproximadas y para centrar el mapa.

    TODO (P2): implementar.
    """
    raise NotImplementedError("P2 · catalogos: centroide de un barrio")


def existe(db: Session, tabla: str, id_: int) -> bool:
    """True si existe una fila con ese id en el catalogo indicado.

    `tabla` es uno de: 'materia', 'etapa_educativa', 'centro_educativo',
    'barrio', 'idioma'.

    Sirve para validar ids que llegan del frontend antes de guardarlos, sin
    que los otros modulos tengan que importar los modelos de catalogos.

    TODO (P2): implementar.
    """
    raise NotImplementedError("P2 · catalogos: validar que un id de catalogo existe")
