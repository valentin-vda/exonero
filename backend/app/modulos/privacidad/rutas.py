from fastapi import APIRouter, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.config import ajustes
from app.dependencias import Db, Yo
from app.modulos.privacidad import esquemas, logica
from app.modulos.privacidad.textos import AVISO_MENORES, AVISO_PRIVACIDAD, HASH_AVISO, VERSION_AVISO


router = APIRouter(prefix="/privacidad", tags=["privacidad"])


@router.get("/aviso", response_model=esquemas.AvisoOut)
def aviso():
    return {
        "version": VERSION_AVISO,
        "hash": HASH_AVISO,
        "aviso": AVISO_PRIVACIDAD,
        "aviso_menores": AVISO_MENORES,
        "modo_demo": ajustes.MODO_DEMO,
        "responsable": ajustes.RESPONSABLE_DATOS,
        "contacto": ajustes.CONTACTO_PRIVACIDAD,
    }


@router.post("/consentimiento-parental", response_model=esquemas.EstadoParentalOut)
def confirmar_parental(datos: esquemas.ConfirmarParentalIn, request: Request, db: Db):
    logica.confirmar_parental(
        db, datos,
        request.client.host if request.client else None,
        request.headers.get("user-agent"),
    )
    db.commit()
    return {"ok": True, "estado": "activa"}


@router.get("/mis-datos")
def mis_datos(yo: Yo, db: Db):
    datos = logica.exportar_datos(db, yo)
    db.commit()
    return JSONResponse(
        content=jsonable_encoder(datos),
        headers={"Content-Disposition": "attachment; filename=exonero-mis-datos.json"},
    )


@router.post("/supresion", status_code=status.HTTP_204_NO_CONTENT)
def suprimir(datos: esquemas.SupresionIn, yo: Yo, db: Db):
    logica.anonimizar(db, yo, datos.clave)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
