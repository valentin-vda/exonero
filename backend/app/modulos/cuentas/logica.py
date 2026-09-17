"""Funciones publicas del modulo cuentas · dueno P1.

cuentas es la unica fuente de la identidad: nadie mas resuelve un token ni
busca un usuario por id. Los otros ocho modulos entran por aca.

Quien consume que:
  - todos      -> obtener_usuario(), para armar la contraparte de una clase,
                  el autor de un mensaje, la persona de una resena
  - perfiles   -> crear_cuenta(), en el alta de cada rol
  - mensajeria -> datos_basicos(), para la cabecera del hilo
"""

from sqlalchemy.orm import Session


def crear_cuenta(db: Session, datos, rol) -> object:
    """Crea la fila en usuario y devuelve el Usuario creado.

    Lo llama el registro de los dos roles. No crea el perfil: de eso se ocupa
    el modulo perfiles, que es quien sabe que columnas lleva cada uno.

    TODO (P1): implementar.
      1. Verificar que el correo no exista -> ErrorAPI(409, "correo_ya_registrado").
      2. Verificar que el documento no exista, si vino -> 409 "documento_ya_registrado".
      3. hash = seguridad.hashear_clave(datos.clave).
      4. Crear Usuario con el rol que llega por parametro, no del cuerpo.
      5. db.add + db.flush para tener el id, SIN commit: el commit lo hace quien
         orquesta el registro, para que la cuenta y el perfil se creen juntos o
         no se cree ninguno.
    """
    raise NotImplementedError("P1 · cuentas: crear la cuenta")


def autenticar(db: Session, correo: str, clave: str) -> object | None:
    """Devuelve el Usuario si las credenciales son correctas, o None.

    Devuelve None tanto si el correo no existe como si la clave esta mal: quien
    llama responde el mismo 409 credenciales_invalidas en los dos casos, para
    no revelar que correos estan registrados.

    TODO (P1): implementar.
      1. Buscar por correo (citext ya ignora mayusculas).
      2. Si no existe -> None.
      3. Si su estado es dada_de_baja -> None.
      4. seguridad.verificar_clave(clave, usuario.hash_clave) -> None si falla.
    """
    raise NotImplementedError("P1 · cuentas: autenticar")


def obtener_usuario(db: Session, usuario_id: int) -> object | None:
    """Devuelve un Usuario por id, o None si no existe.

    Es la funcion que mas se llama de todo el sistema. La usan los otros ocho
    modulos para resolver a la otra persona sin importar cuentas/modelos.py.

    TODO (P1): implementar.
    """
    raise NotImplementedError("P1 · cuentas: obtener usuario por id")


def datos_basicos(db: Session, usuario_id: int) -> dict | None:
    """Version liviana de un usuario: id, nombre, apellido, foto y rol.

    Es lo que necesitan las tarjetas y las cabeceras de los otros modulos: la
    contraparte de una clase, la otra persona de un hilo. Devuelve un dict en
    vez del modelo, justamente para que nadie dependa de la forma de la tabla.

    TODO (P1): implementar.
    """
    raise NotImplementedError("P1 · cuentas: datos basicos de un usuario")


def es_menor(db: Session, usuario_id: int) -> bool:
    """True si el usuario tiene menos de 18 anios segun fecha_nacimiento.

    Lo usa perfiles para decidir si el adulto responsable es obligatorio.
    Si fecha_nacimiento es NULL devuelve False: no se puede afirmar que es menor.

    TODO (P1): implementar.
    """
    raise NotImplementedError("P1 · cuentas: saber si es menor de edad")
