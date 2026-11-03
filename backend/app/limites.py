"""Limitador pequeno para el despliegue local de un solo proceso."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic

_eventos: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_candado = Lock()

LIMITES = {
    "/api/auth/login": 30,
    "/api/auth/recuperar": 8,
    "/api/auth/restablecer": 8,
    "/api/auth/registro/estudiante": 8,
    "/api/auth/registro/profesor": 8,
    "/api/privacidad/consentimiento-parental": 8,
}


def excedido(ip: str, ruta: str) -> bool:
    limite = LIMITES.get(ruta)
    if limite is None:
        return False
    instante = monotonic()
    clave = (ip, ruta)
    with _candado:
        cola = _eventos[clave]
        while cola and cola[0] < instante - 60:
            cola.popleft()
        if len(cola) >= limite:
            return True
        cola.append(instante)
    return False
