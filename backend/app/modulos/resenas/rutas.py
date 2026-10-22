"""Rutas HTTP del modulo resenas - dueno P3.

Todo cuelga de /api/resenas.

Un solo par de endpoints para los dos sentidos: quien resena a quien sale del
rol del token, no del cuerpo.

Igual que en el resto: cada ruta llama a logica.py, hace el commit y responde.
"""

from fastapi import APIRouter, Query, status

from app.dependencias import Db, Yo
from app.modulos.resenas import esquemas, logica

router = APIRouter(prefix="/resenas", tags=["resenas"])


@router.post("", response_model=esquemas.ResenaOut, status_code=status.HTTP_201_CREATED)
def dejar_resena(datos: esquemas.ResenaIn, yo: Yo, db: Db):
    """Deja una resena. Compartido por 1b (alumno) y 1i (profesor).

    Anonima, sobre la persona y no sobre una clase, una sola por par y por
    sentido.

    Errores: 409 ya_resenado (usar PUT para editarla),
             403 sin_clases_con_esa_persona.
    """
    resena = logica.dejar_o_editar(db, yo.id, yo.rol, datos, crear=True)
    db.commit()
    return resena


@router.put("", response_model=esquemas.ResenaOut)
def editar_resena(datos: esquemas.ResenaIn, yo: Yo, db: Db):
    """Edita la resena que uno ya dejo. Compartido por 1b y 1i.

    Se puede editar justamente porque el autor se guarda en la tabla.

    Errores: 404 resena_no_existe, 403 sin_clases_con_esa_persona.
    """
    resena = logica.dejar_o_editar(db, yo.id, yo.rol, datos, crear=False)
    db.commit()
    return resena


@router.get("/resumen/{usuario_id}", response_model=esquemas.ResumenResenasOut)
def resumen_resenas(usuario_id: int, db: Db):
    """Promedio, cantidad y distribucion. 1d, 1e, 1f, 1i y 1j.

    Mismo contrato para un profesor y para un alumno.

    Si alguien agrega /resenas/{id}, tiene que ir despues de estas dos.

    Error: 404 usuario_no_existe.
    """
    return logica.resumen(db, usuario_id)


@router.get("/usuario/{usuario_id}", response_model=esquemas.PaginaResenasOut)
def resenas_de_usuario(usuario_id: int, db: Db, orden: str = "recientes", pagina: int = Query(1, ge=1)):
    """Las resenas que recibio una persona, paginadas de a diez. 1e y 1f.

    SIN AUTOR, sin id de autor, sin nada que permita deducir quien la escribio.
    Solo puntaje, comentario y fecha.

    Errores: 400 orden_invalido (orden es recientes o puntaje), 404 usuario_no_existe.
    """
    return logica.pagina(db, usuario_id, orden, pagina)
