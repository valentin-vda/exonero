"""Rutas HTTP del modulo mensajeria - dueno P3.

Todo cuelga de /api/mensajes. Chat directo entre alumno y profesor.

OJO CON EL ORDEN: /no-leidos va ANTES que /hilos/{id}, porque si no FastAPI
puede intentar resolverlo como un id.
"""

from fastapi import APIRouter, status

from app.dependencias import Db, Yo
from app.modulos.mensajeria import esquemas

router = APIRouter(prefix="/mensajes", tags=["mensajeria"])


@router.get("/no-leidos", response_model=esquemas.NoLeidosOut)
def no_leidos(yo: Yo, db: Db):
    """El contador de la cabecera. Vive en LAS DIEZ PANTALLAS.

    El frontend lo consulta cada diez segundos, asi que tiene que ser barato.

    TODO (P3): implementar. Envolver logica.contar_no_leidos().
    """
    raise NotImplementedError("P3 - mensajeria: GET /mensajes/no-leidos")


@router.get("/hilos", response_model=list[esquemas.HiloOut])
def bandeja(yo: Yo, db: Db, q: str | None = None):
    """La bandeja de 1h, ordenada por actividad.

    Ordena por ultimo_mensaje_el (la columna desnormalizada del hilo), no por
    un MAX sobre mensaje.

    `q` filtra por nombre de la otra persona.

    TODO (P3): implementar. Cuidado con el N+1: el contador de no leidos de
    cada hilo se resuelve con un GROUP BY, no con una consulta por hilo.
    """
    raise NotImplementedError("P3 - mensajeria: GET /mensajes/hilos")


@router.post("/hilos", response_model=esquemas.HiloOut, status_code=status.HTTP_201_CREATED)
def abrir_hilo(datos: esquemas.AbrirHiloIn, yo: Yo, db: Db):
    """Abre la conversacion con un profesor. Es el boton de contactar de 1f.

    Devuelve el hilo EXISTENTE si ya lo hay. No crea uno nuevo cada vez.

    TODO (P3): implementar. Envolver logica.obtener_o_crear_hilo().
    """
    raise NotImplementedError("P3 - mensajeria: POST /mensajes/hilos")


@router.get("/hilos/{hilo_id}/mensajes", response_model=list[esquemas.MensajeOut])
def mensajes_del_hilo(hilo_id: int, yo: Yo, db: Db, antes: int | None = None, limite: int = 30):
    """El historial, paginado hacia atras. 1h.

    ESTE GET MARCA COMO LEIDOS todos los mensajes del hilo, en el mismo
    llamado. No hay una accion aparte de "marcar como leido": abrir el hilo es
    leerlo.

    `antes` es el id del mensaje mas viejo que ya tiene el frontend; se usa
    para el scroll infinito hacia arriba.

    TODO (P3): implementar.
      1. 403 si el hilo no es de esta persona.
      2. Traer los mensajes anteriores a `antes`, ordenados por enviado_el desc.
      3. logica.marcar_leidos(db, hilo_id, yo.id).
    """
    raise NotImplementedError("P3 - mensajeria: GET /mensajes/hilos/{id}/mensajes")


@router.post("/hilos/{hilo_id}/mensajes", response_model=esquemas.MensajeOut,
             status_code=status.HTTP_201_CREATED)
def enviar_mensaje(hilo_id: int, datos: esquemas.EnviarMensajeIn, yo: Yo, db: Db):
    """Envia un mensaje. 1h.

    TODO (P3): implementar.
      1. 403 si el hilo no es de esta persona.
      2. Rechazar texto vacio -> 400.
      3. Insertar el mensaje Y actualizar hilo.ultimo_mensaje_el. Las dos
         cosas juntas, o la bandeja se desordena.
    """
    raise NotImplementedError("P3 - mensajeria: POST /mensajes/hilos/{id}/mensajes")
