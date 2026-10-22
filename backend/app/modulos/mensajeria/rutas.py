"""Rutas HTTP del modulo mensajeria - dueno P3.

Todo cuelga de /api/mensajes. Chat directo entre alumno y profesor.

OJO CON EL ORDEN: /no-leidos va ANTES que /hilos/{id}, porque si no FastAPI
puede intentar resolverlo como un id.

Igual que en el resto: cada ruta llama a logica.py, hace el commit y responde.
"""

from fastapi import APIRouter, Query, Response, status

from app.dependencias import Db, Yo
from app.enums import Rol
from app.errores import ErrorAPI
from app.modulos.mensajeria import esquemas, logica

router = APIRouter(prefix="/mensajes", tags=["mensajeria"])


@router.get("/no-leidos", response_model=esquemas.NoLeidosOut)
def no_leidos(yo: Yo, db: Db):
    """El contador de la cabecera. Vive en LAS DIEZ PANTALLAS.

    El frontend lo consulta cada diez segundos, asi que es un solo COUNT.
    """
    return {"no_leidos": logica.contar_no_leidos(db, yo.id)}


@router.get("/hilos", response_model=list[esquemas.HiloOut])
def bandeja(yo: Yo, db: Db, q: str | None = None):
    """La bandeja de 1h, ordenada por actividad.

    `q` filtra por nombre de la otra persona (sin importar tildes).
    """
    return logica.bandeja(db, yo.id, q)


@router.post(
    "/hilos",
    response_model=esquemas.HiloOut,
    status_code=status.HTTP_201_CREATED,
    responses={200: {"description": "El hilo ya existia: se devuelve el mismo"}},
)
def abrir_hilo(datos: esquemas.AbrirHiloIn, yo: Yo, db: Db, response: Response):
    """Abre la conversacion con otra persona. El boton de contactar de 1f, y
    el "Mensaje" de 1a y 1d.

    Devuelve el hilo EXISTENTE si ya lo hay (200), o uno nuevo (201).

    Errores: 400 datos_invalidos (no vino el id del rol que corresponde),
             404 profesor_no_existe / estudiante_no_existe,
             403 sin_clases_con_esa_persona (un profe con un alumno sin clases).
    """
    otro_id = datos.profesor_id if yo.rol == Rol.estudiante else datos.estudiante_id
    if otro_id is None:
        raise ErrorAPI(400, "datos_invalidos")
    hilo, creado = logica.obtener_o_crear_hilo(db, yo, otro_id)
    db.commit()
    if not creado:
        response.status_code = status.HTTP_200_OK
    return logica.fila_de_hilo(db, hilo, yo.id)


@router.get("/hilos/{hilo_id}/mensajes", response_model=list[esquemas.MensajeOut])
def mensajes_del_hilo(hilo_id: int, yo: Yo, db: Db, antes: int | None = None,
                      limite: int = Query(30, ge=1, le=logica.LIMITE_MAXIMO)):
    """El historial, paginado hacia atras, en orden cronologico. 1h.

    ESTE GET MARCA COMO LEIDOS los mensajes del otro en el hilo, en el mismo
    llamado: abrir el hilo es leerlo.

    `antes` es el id del mensaje mas viejo que ya tiene el frontend; se usa
    para el "Cargar anteriores".

    Errores: 404 hilo_no_existe, 403 no_es_tuyo.
    """
    hilo = logica.hilo_propio(db, hilo_id, yo.id)
    pagina = logica.mensajes(db, hilo, yo.id, antes, limite)
    db.commit()
    return pagina


@router.post("/hilos/{hilo_id}/mensajes", response_model=esquemas.MensajeOut,
             status_code=status.HTTP_201_CREATED)
def enviar_mensaje(hilo_id: int, datos: esquemas.EnviarMensajeIn, yo: Yo, db: Db):
    """Envia un mensaje. 1h.

    Errores: 404 hilo_no_existe, 403 no_es_tuyo, 400 mensaje_vacio,
             422 si pasa de 2000 caracteres.
    """
    hilo = logica.hilo_propio(db, hilo_id, yo.id)
    mensaje = logica.enviar(db, hilo, yo.id, datos.texto)
    db.commit()
    return mensaje
