"""Punto de entrada de la API.

Crea la aplicacion FastAPI, monta los routers de los nueve modulos bajo /api y
deja la documentacion interactiva en http://localhost:8000/docs.

Se levanta con:  uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import ajustes
from app.limites import excedido

if not ajustes.MODO_DEMO:
    raise RuntimeError(
        "Este prototipo no puede iniciar fuera de MODO_DEMO: falta identificar "
        "al responsable, registrar las bases y reemplazar el pago ficticio."
    )

# Importar el registro hace que las 24 tablas queden en Base.metadata.
# Tiene que pasar ANTES de montar los routers.
from app import registro_modelos  # noqa: F401

from app.modulos.agenda.rutas import router as router_agenda
from app.modulos.busqueda.rutas import router as router_busqueda
from app.modulos.catalogos.rutas import router as router_catalogos
from app.modulos.clases.rutas import router as router_clases
from app.modulos.cuentas.rutas import router_auth, router_usuarios
from app.modulos.mensajeria.rutas import router as router_mensajes
from app.modulos.pagos.rutas import router as router_pagos
from app.modulos.perfiles.rutas import router_perfiles, router_profesores
from app.modulos.resenas.rutas import router as router_resenas
from app.modulos.privacidad.rutas import router as router_privacidad

app = FastAPI(
    title="Exonero API",
    version="0.1.0",
    description=(
        "Plataforma de clases particulares. Nueve modulos con frontera de "
        "microservicio: cuentas, perfiles, catalogos, busqueda, agenda, "
        "clases, pagos, mensajeria y resenas."
    ),
    docs_url="/docs",
    redoc_url=None,
)

# El dev server de Vite corre en otro puerto, asi que el navegador manda un
# preflight OPTIONS antes de cada llamada. Sin esto, todas fallan.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ajustes.cors_lista,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Todos los routers cuelgan de /api, como fija la spec.
# El orden de esta lista no importa; lo que importa es el orden de las rutas
# DENTRO de cada router (las literales antes que las de {id}).
app.include_router(router_auth, prefix="/api")
app.include_router(router_usuarios, prefix="/api")
app.include_router(router_perfiles, prefix="/api")
app.include_router(router_profesores, prefix="/api")
app.include_router(router_catalogos, prefix="/api")
app.include_router(router_busqueda, prefix="/api")
app.include_router(router_agenda, prefix="/api")
app.include_router(router_clases, prefix="/api")
app.include_router(router_pagos, prefix="/api")
app.include_router(router_mensajes, prefix="/api")
app.include_router(router_resenas, prefix="/api")
app.include_router(router_privacidad, prefix="/api")


@app.middleware("http")
async def cabeceras_seguridad(request, call_next):
    ip = request.client.host if request.client else "desconocida"
    if excedido(ip, request.url.path):
        return JSONResponse({"detail": "demasiados_intentos"}, status_code=429)
    respuesta = await call_next(request)
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["X-Frame-Options"] = "DENY"
    respuesta.headers["Referrer-Policy"] = "no-referrer"
    respuesta.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
    respuesta.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if request.headers.get("authorization") or request.url.path.startswith("/api/privacidad"):
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@app.get("/api/salud", tags=["sistema"])
def salud():
    """Prueba de vida. Sirve para confirmar que el backend levanto antes de
    empezar a pelearse con el frontend."""
    return {"estado": "ok", "servicio": "exonero-api"}
