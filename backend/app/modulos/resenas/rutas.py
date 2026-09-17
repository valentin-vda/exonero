"""Rutas HTTP del modulo resenas - dueno P3.

Todo cuelga de /api/resenas.

Un solo par de endpoints para los dos sentidos: quien resena a quien sale del
rol del token, no del cuerpo.
"""

from fastapi import APIRouter, status

from app.dependencias import Db, Yo
from app.modulos.resenas import esquemas

router = APIRouter(prefix="/resenas", tags=["resenas"])


@router.post("", response_model=esquemas.ResenaOut, status_code=status.HTTP_201_CREATED)
def dejar_resena(datos: esquemas.ResenaIn, yo: Yo, db: Db):
    """Deja una resena. Compartido por 1b (alumno) y 1i (profesor).

    Anonima, sobre la persona y no sobre una clase, una sola por par y por
    sentido.

    Errores: 409 ya_resenado (usar PUT para editarla),
             403 sin_clases_con_esa_persona.

    TODO (P3): implementar. Envolver logica.dejar_o_editar().
    """
    raise NotImplementedError("P3 - resenas: POST /resenas")


@router.put("", response_model=esquemas.ResenaOut)
def editar_resena(datos: esquemas.ResenaIn, yo: Yo, db: Db):
    """Edita la resena que uno ya dejo. Compartido por 1b y 1i.

    Se puede editar justamente porque el autor se guarda en la tabla.

    TODO (P3): implementar.
    """
    raise NotImplementedError("P3 - resenas: PUT /resenas")


@router.get("/resumen/{usuario_id}", response_model=esquemas.ResumenResenasOut)
def resumen_resenas(usuario_id: int, db: Db):
    """Promedio, cantidad y distribucion. 1d, 1e, 1f, 1i y 1j.

    Mismo contrato para un profesor y para un alumno.

    OJO CON EL ORDEN: /resumen/{id} va ANTES que /usuario/{id}? No hace falta,
    son prefijos distintos. Pero si alguien agrega /resenas/{id}, tiene que ir
    despues de estas dos.

    TODO (P3): implementar. Envolver logica.resumen().
    """
    raise NotImplementedError("P3 - resenas: GET /resenas/resumen/{usuario_id}")


@router.get("/usuario/{usuario_id}", response_model=esquemas.PaginaResenasOut)
def resenas_de_usuario(usuario_id: int, db: Db, orden: str = "recientes", pagina: int = 1):
    """Las resenas que recibio una persona, paginadas. 1e y 1f.

    SIN AUTOR, sin id de autor, sin nada que permita deducir quien la escribio.
    Solo puntaje, comentario y fecha.

    TODO (P3): implementar. orden: recientes o puntaje.
    """
    raise NotImplementedError("P3 - resenas: GET /resenas/usuario/{id}")
