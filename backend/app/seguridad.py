"""Hash de contrasenas y firma de tokens.

Dos responsabilidades chicas que necesita el modulo cuentas, separadas aca
para que se puedan probar solas y para que ningun otro modulo tenga que saber
como se hashea o como se firma.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import ajustes


# --- Contrasenas ------------------------------------------------------------

def hashear_clave(clave: str) -> str:
    """Devuelve el hash bcrypt de una contrasena en texto plano.

    Es lo que se guarda en usuario.hash_clave. La contrasena en texto plano no
    se guarda nunca, ni siquiera en logs.
    """
    return bcrypt.hashpw(clave.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_clave(clave: str, hash_guardado: str) -> bool:
    """True si la contrasena en texto plano corresponde al hash guardado."""
    try:
        return bcrypt.checkpw(clave.encode("utf-8"), hash_guardado.encode("utf-8"))
    except ValueError:
        # hash_guardado corrupto o vacio: se trata como credencial invalida.
        return False


# --- Tokens -----------------------------------------------------------------

def crear_token(usuario_id: int, rol: str) -> tuple[str, int]:
    """Firma un JWT con el id y el rol del usuario.

    Devuelve (token, segundos_hasta_vencer), que es exactamente lo que
    POST /auth/login tiene que responder.

    El token no se guarda en la base: no hay sesiones. Vive en el frontend y
    vence solo.
    """
    vence = datetime.now(timezone.utc) + timedelta(hours=ajustes.JWT_HORAS_VALIDO)
    carga = {"sub": str(usuario_id), "rol": rol, "exp": vence}
    token = jwt.encode(carga, ajustes.JWT_SECRETO, algorithm=ajustes.JWT_ALGORITMO)
    return token, ajustes.JWT_HORAS_VALIDO * 3600


def leer_token(token: str) -> dict | None:
    """Valida la firma y el vencimiento y devuelve la carga del token.

    Devuelve None si el token es invalido o vencido; quien llama decide si eso
    es un 401. No levanta excepciones para que el caller controle el flujo.
    """
    try:
        return jwt.decode(token, ajustes.JWT_SECRETO, algorithms=[ajustes.JWT_ALGORITMO])
    except jwt.PyJWTError:
        return None
