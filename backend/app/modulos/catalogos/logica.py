"""Funciones publicas del modulo catalogos · dueno P2.

Esto es lo que pueden llamar los otros modulos. Todo lo demas de catalogos es
privado. La otra puerta de entrada es rutas.py, que usa el frontend.

Quien consume que:
  - clases  -> parametros_vigentes(), para congelar comision e IVA en la clase
  - busqueda -> centroide_barrio(), para ordenar por cercania
"""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modulos.catalogos import modelos

def parametros_vigentes(db: Session) -> dict[str, Decimal]:
    """Devuelve la comision de servicio y la tasa de IVA vigentes hoy.
    Formato: {"comision_servicio": Decimal("10.00"), "tasa_iva": Decimal("22.00")}
    Es lo que POST /clases/cotizar y POST /clases usan para armar el desglose.
    Los porcentajes se guardan congelados en la clase: si manana cambia la
    comision, las clases ya creadas siguen valiendo lo mismo.
      1. Por cada clave ('comision_servicio', 'tasa_iva') buscar la fila con
         el vigente_desde mas grande que sea <= hoy.
      2. Armar el diccionario. Si falta alguna clave, levantar un error claro:
         sin estos valores no se puede cotizar nada.
    """
    resultado: dict[str, Decimal] = {}
    claves = ("comision_servicio", "tasa_iva")

    for clave in claves:
        consulta = (
            select(modelos.ParametroPlataforma.valor)
            .where(modelos.ParametroPlataforma.clave == clave)
            .where(modelos.ParametroPlataforma.vigente_desde <= date.today())
            .order_by(modelos.ParametroPlataforma.vigente_desde.desc())
            .limit(1)
        )
        valor = db.scalar(consulta)
        if valor is None:
            raise RuntimeError(f"Falta el parametro vigente: {clave}")
        resultado[clave] = valor

    return resultado


def centroide_barrio(db: Session, barrio_id: int) -> tuple[Decimal, Decimal] | None:
    """Devuelve (latitud, longitud) del centroide de un barrio, o None.
    Lo usa busqueda para calcular distancias aproximadas y para centrar el mapa.
    """
    consulta = (select(modelos.Barrio.latitud,modelos.Barrio.longitud)
                .where(modelos.Barrio.id == barrio_id))
    fila = db.execute(consulta).one_or_none()
    #one_or_none(): Si encuentra exactamente una fila, la devuelve.
    #               Si no encuentra ninguna, devuelve None.
    #               Si encuentra más de una, lanza un error MultipleResultsFound.
    if fila is None or fila.latitud is None or fila.longitud is None:
        return None
    return fila.latitud, fila.longitud


def existe(db: Session, tabla: str, id_: int) -> bool:
    """True si existe una fila con ese id en el catalogo indicado.
    `tabla` es uno de: 'materia', 'etapa_educativa', 'centro_educativo',
    'barrio', 'idioma'.
    Sirve para validar ids que llegan del frontend antes de guardarlos, sin
    que los otros modulos tengan que importar los modelos de catalogos.
    """
    modelos_por_tabla = {
        "materia": modelos.Materia,
        "etapa_educativa": modelos.EtapaEducativa,
        "centro_educativo": modelos.CentroEducativo,
        "barrio": modelos.Barrio,
        "idioma": modelos.Idioma,
    }
    modelo = modelos_por_tabla.get(tabla)
    if modelo is None:
        return False
    consulta = select(modelo.id).where(modelo.id == id_)
    return db.scalar(consulta) is not None
