"""Los trece tipos ENUM de PostgreSQL, como enumeraciones de Python.

Estan todos aca y no dentro de cada modulo porque varios modulos usan los
mismos (modalidad_enum la usan perfiles, agenda y clases). Es la unica pieza
compartida ademas de los catalogos: importar esto NO rompe la regla de
"nadie importa modelos.py de otro modulo", porque aca no hay tablas.
"""

import enum


class Rol(str, enum.Enum):
    """Una cuenta es alumno o profesor, y no cambia. Quien quiera ser las dos
    cosas se crea dos cuentas con dos correos."""
    estudiante = "estudiante"
    profesor = "profesor"


class EstadoCuenta(str, enum.Enum):
    """La baja es logica: la cuenta queda inactiva y las clases pasadas se
    conservan."""
    activa = "activa"
    dada_de_baja = "dada_de_baja"


class Tema(str, enum.Enum):
    claro = "claro"
    oscuro = "oscuro"


class TipoCentro(str, enum.Enum):
    escuela = "escuela"
    liceo = "liceo"
    utu = "utu"
    facultad = "facultad"
    instituto = "instituto"


class Modalidad(str, enum.Enum):
    """En perfil_profesor y franja_disponibilidad puede ser 'ambas'.
    En clase NO: una clase concreta es presencial u online (CHECK en la tabla)."""
    presencial = "presencial"
    online = "online"
    ambas = "ambas"


class LugarClase(str, enum.Enum):
    espacio_propio = "espacio_propio"
    a_domicilio = "a_domicilio"
    ambos = "ambos"
    espacio_publico = "espacio_publico"


class Formato(str, enum.Enum):
    """Lo grupal esta fuera de v1: el formulario lo guarda y nada mas lo lee."""
    individual = "individual"
    grupal = "grupal"
    ambos = "ambos"


class EstadoFicha(str, enum.Enum):
    """Solo las publicadas aparecen en la busqueda."""
    borrador = "borrador"
    publicada = "publicada"
    pausada = "pausada"


class EstadoClase(str, enum.Enum):
    """El ciclo de vida completo de una clase.

    pendiente  -> recien creada por el alumno, el profesor todavia no respondio
    aprobada   -> el profesor la acepto; ocupa el horario en la agenda
    cancelada  -> alguna de las dos partes la cancelo; NO se borra, queda en el
                  historial porque el reembolso y la tasa de cancelacion la
                  necesitan
    dictada    -> el profesor la marco como dada
    no_asistida-> el alumno no vino

    La clase RECHAZADA no es un estado: la fila se borra.
    """
    pendiente = "pendiente"
    aprobada = "aprobada"
    cancelada = "cancelada"
    dictada = "dictada"
    no_asistida = "no_asistida"


class Actor(str, enum.Enum):
    """Quien cancelo la clase. Sale del rol del token."""
    estudiante = "estudiante"
    profesor = "profesor"


class EstadoCobro(str, enum.Enum):
    """El dinero de una clase, que es lo unico que vive en la tabla cobro.

    retenido    -> al crear la clase (el alumno ya puso la tarjeta)
    cobrado     -> cuando el profesor aprueba
    liberado    -> cuando el profesor rechaza (la clase se borra, el cobro queda)
    reembolsado -> cuando se cancela una clase aprobada
    """
    retenido = "retenido"
    cobrado = "cobrado"
    liberado = "liberado"
    reembolsado = "reembolsado"


class SentidoResena(str, enum.Enum):
    """Las resenas van en los dos sentidos. El sentido sale del rol del token,
    no lo manda el frontend."""
    alumno_a_profesor = "alumno_a_profesor"
    profesor_a_alumno = "profesor_a_alumno"
