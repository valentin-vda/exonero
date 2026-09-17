"""Errores de la API, con el formato unico que fija la seccion 9 de la spec.

Toda respuesta de error es {"detail": "codigo_corto"} en snake_case, para que
el frontend pueda decidir que mensaje mostrar sin parsear texto en espanol.

    400 datos invalidos
    401 sin token o vencido
    403 no es tuyo
    404 no existe
    409 conflicto de estado
    422 falla de validacion (la tira FastAPI sola)
"""

from fastapi import HTTPException


class ErrorAPI(HTTPException):
    """Error con codigo corto y estable. Se levanta asi:

        raise ErrorAPI(409, "horario_ocupado")
    """

    def __init__(self, codigo_http: int, detalle: str):
        super().__init__(status_code=codigo_http, detail=detalle)


# --- Atajos para los errores que se repiten en varios modulos ---------------

def sin_autorizacion() -> ErrorAPI:
    return ErrorAPI(401, "sin_token")


def no_es_tuyo() -> ErrorAPI:
    return ErrorAPI(403, "no_es_tuyo")


def no_existe(que: str = "recurso") -> ErrorAPI:
    return ErrorAPI(404, f"{que}_no_existe")


def conflicto(codigo: str) -> ErrorAPI:
    return ErrorAPI(409, codigo)
