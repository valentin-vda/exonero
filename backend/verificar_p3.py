"""Comprobaciones de P3 (agenda, mensajeria y resenas) contra un backend levantado.

Igual que verificar_p4.py: se corre desde backend/, con el venv, contra una
base de PRUEBA recien sembrada (alembic upgrade head + python -m app.seeds) y
un uvicorn levantado contra esa misma base:

    python verificar_p3.py                          # contra http://127.0.0.1:8001
    python verificar_p3.py http://127.0.0.1:8000

Cubre agenda (1i): los huecos libres con todas sus reglas, cada motivo de
verificar, las franjas, los bloqueos, el calendario semanal y lo que consumen
busqueda, clases y perfiles. Resenas (1b, 1i, 1e, 1f): las reglas de alta,
el recalculo del promedio, el anonimato y la paginacion. Y mensajeria (1h y
la cabecera): quien puede abrir un hilo, el contador de no leidos, abrir es
leer, el historial hacia atras, la busqueda y que la bandeja no haga N+1.

OJO: ensucia la base (cambia reglas y franjas de profe1, crea bloqueos) y al
final la vuelve a sembrar. Por eso se niega a correr si el .env apunta a la
base "exonero" (la de todos los dias), salvo con --forzar. Usar una aparte:
exonero_p3, por ejemplo.
"""

import json
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, time, timedelta

from sqlalchemy import text

from app import fechas
from app.config import ajustes
from app.db import SesionLocal

if ajustes.BASE_URL.rsplit("/", 1)[-1] == "exonero" and "--forzar" not in sys.argv:
    sys.exit("El .env apunta a la base 'exonero'. Esto la ensucia y la vuelve a sembrar: "
             "correlo contra una base de prueba (por ejemplo exonero_p3), o con --forzar.")

# 127.0.0.1 y no localhost: en Windows, "localhost" prueba primero IPv6 (::1),
# uvicorn escucha solo en IPv4, y cada llamada pierde dos segundos esperando.
_URLS = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (_URLS[0] if _URLS else "http://127.0.0.1:8001").rstrip("/") + "/api"
CLAVE = "exonero123"

pasaron = 0
fallaron: list[str] = []


# ---------------------------------------------------------------------------
# Herramientas (las mismas de verificar_p4.py)
# ---------------------------------------------------------------------------

def pedir(metodo: str, ruta: str, cuerpo=None, token: str | None = None):
    """(codigo HTTP, JSON o None). Nunca levanta por un 4xx/5xx."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo)
    if datos is not None:
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as r:
            crudo = r.read()
            return r.status, (json.loads(crudo) if crudo else None)
    except urllib.error.HTTPError as e:
        crudo = e.read()
        try:
            return e.code, json.loads(crudo)
        except ValueError:
            return e.code, crudo.decode(errors="replace")


def ok(nombre: str, condicion: bool, detalle="") -> bool:
    global pasaron
    if condicion:
        pasaron += 1
    else:
        fallaron.append(f"{nombre}  {detalle}")
        print(f"  FALLA  {nombre}  {detalle}")
    return condicion


def error(nombre: str, respuesta, codigo_http: int, detalle: str):
    """Chequea que una respuesta sea {"detail": detalle} con ese codigo."""
    estado, cuerpo = respuesta
    ok(nombre, estado == codigo_http and isinstance(cuerpo, dict) and cuerpo.get("detail") == detalle,
       f"esperaba {codigo_http} {detalle}, vino {estado} {cuerpo}")


def sql(consulta: str, **parametros):
    """La primera columna de la primera fila (o None)."""
    with SesionLocal() as db:
        return db.execute(text(consulta), parametros).scalar()


def ejecutar(consulta: str, **parametros) -> None:
    """Un UPDATE directo en la base, con commit."""
    with SesionLocal() as db:
        db.execute(text(consulta), parametros)
        db.commit()


def filas(consulta: str, **parametros) -> list:
    with SesionLocal() as db:
        return db.execute(text(consulta), parametros).all()


def login(correo: str) -> str:
    estado, cuerpo = pedir("POST", "/auth/login", {"correo": correo, "clave": CLAVE})
    assert estado == 200, (correo, estado, cuerpo)
    return cuerpo["token"]


def seccion(titulo: str):
    print(f"\n== {titulo}")


def dia_habil(dias: int) -> date:
    """hoy + dias, corrido al lunes si cae en fin de semana."""
    dia = fechas.ahora().date() + timedelta(days=dias)
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return dia


def iso(dia: date, hora: int, minuto: int = 0) -> str:
    return datetime.combine(dia, time(hora, minuto), fechas.ZONA).isoformat()


def momento(texto: str) -> datetime:
    return datetime.fromisoformat(texto).astimezone(fechas.ZONA)


def disponibilidad(profesor_id: int, desde: date, hasta: date, duracion: int = 60):
    return pedir("GET", f"/agenda/profesores/{profesor_id}/disponibilidad"
                        f"?desde={desde}&hasta={hasta}&duracion={duracion}")


def huecos_de(respuesta) -> list[tuple[datetime, datetime]]:
    """Todos los huecos de una respuesta de disponibilidad, como datetimes."""
    return [(momento(h["inicio"]), momento(h["fin"])) for d in respuesta for h in d["huecos"]]


def verificar(profesor_id: int, inicio: str, duracion: int = 60):
    return pedir("POST", "/agenda/verificar",
                 {"profesor_id": profesor_id, "inicio": inicio, "duracion_min": duracion})


def se_pisan(a: tuple[datetime, datetime], b: tuple[datetime, datetime]) -> bool:
    return a[0] < b[1] and b[0] < a[1]


# ---------------------------------------------------------------------------
# Usuarios y datos de los seeds
# ---------------------------------------------------------------------------

ID = {
    correo.split("@")[0]: id_
    for id_, correo in filas("SELECT id, correo FROM usuario")
}
PERFIL1 = sql("SELECT id FROM perfil_profesor WHERE usuario_id = :u", u=ID["profe1"])
profe1, profe2, alumno1 = login("profe1@example.com"), login("profe2@example.com"), login("alumno1@example.com")

# La primera aprobada de profe1 en un dia habil, a mas de un dia, y en un dia
# sin bloqueos: con los seeds grandes hay muchas, y algunas caen un sabado o
# el dia del "Turno medico", donde los chequeos de abajo ("otra hora del dia
# de la aprobada") darian otro motivo.
APROBADA = filas(
    "SELECT c.id, c.inicio, c.fin FROM clase c WHERE c.profesor_id = :p AND c.estado = 'aprobada' "
    "AND c.inicio > now() + interval '1 day' "
    "AND extract(isodow FROM c.inicio AT TIME ZONE 'America/Montevideo') <= 5 "
    "AND NOT EXISTS (SELECT 1 FROM bloqueo b WHERE b.perfil_profesor_id = :perfil "
    "AND (b.inicio AT TIME ZONE 'America/Montevideo')::date = (c.inicio AT TIME ZONE 'America/Montevideo')::date) "
    "ORDER BY c.inicio", p=ID["profe1"], perfil=PERFIL1)[0]
PENDIENTE = filas("SELECT id, inicio, fin FROM clase WHERE profesor_id = :p AND estado = 'pendiente'", p=ID["profe1"])[0]
FRANJAS_ORIGINALES = [
    {"dia_semana": f.dia_semana, "hora_inicio": f.hora_inicio.isoformat(), "hora_fin": f.hora_fin.isoformat(),
     "modalidad": f.modalidad, "activa": f.activa}
    for f in filas("SELECT dia_semana, hora_inicio, hora_fin, modalidad::text AS modalidad, activa "
                   "FROM franja_disponibilidad WHERE perfil_profesor_id = :p ORDER BY dia_semana, hora_inicio",
                   p=PERFIL1)
]
HOY = fechas.ahora().date()


def reglas(**valores):
    """Cambia reglas de profe1 directo en la base (las de 1j son de P1)."""
    asignaciones = ", ".join(f"{k} = :{k}" for k in valores)
    ejecutar(f"UPDATE perfil_profesor SET {asignaciones} WHERE id = :p", p=PERFIL1, **valores)


# ===========================================================================
# GET /agenda/profesores/{id}/disponibilidad
# ===========================================================================

seccion("Disponibilidad: errores")
error("hasta antes que desde", disponibilidad(ID["profe1"], HOY, HOY - timedelta(days=1)), 400, "rango_invalido")
error("mas de 31 dias", disponibilidad(ID["profe1"], HOY, HOY + timedelta(days=31)), 400, "rango_invalido")
error("profesor que no existe", disponibilidad(99999, HOY, HOY), 404, "profesor_no_existe")
error("un alumno no tiene agenda", disponibilidad(ID["alumno1"], HOY, HOY), 404, "profesor_no_existe")
estado, _ = disponibilidad(ID["profe1"], HOY, HOY, duracion=5)
ok("duracion menor a 15: 422", estado == 422, estado)

seccion("Disponibilidad: las reglas")
desde, hasta = HOY, HOY + timedelta(days=13)
estado, dias = disponibilidad(ID["profe1"], desde, hasta)
ok("200 con los 14 dias del rango, en orden", estado == 200
   and [d["fecha"] for d in dias] == [(desde + timedelta(days=n)).isoformat() for n in range(14)], estado)
huecos = huecos_de(dias)
ok("hay huecos", len(huecos) > 10, len(huecos))
ok("cada hueco dura lo pedido", all(f - i == timedelta(minutes=60) for i, f in huecos))
ok("arrancan en :00 o :30", all(i.minute in (0, 30) and i.second == 0 for i, _ in huecos))
ok("no se pisan entre si", all(not se_pisan(a, b) for a, b in zip(huecos, huecos[1:])))
franjas = filas("SELECT dia_semana, hora_inicio, hora_fin FROM franja_disponibilidad WHERE perfil_profesor_id = :p",
                p=PERFIL1)
ok("todos caen adentro de una franja de ese dia de la semana", all(
    any(f.dia_semana == i.isoweekday() % 7 and f.hora_inicio <= i.time() and fin.time() <= f.hora_fin
        for f in franjas)
    for i, fin in huecos))
ok("ninguno el domingo (profe1 no tiene franja)", all(i.isoweekday() != 7 for i, _ in huecos))
ok("ninguno antes de ahora + aviso minimo (12 h)", all(i >= fechas.ahora() + timedelta(hours=12) for i, _ in huecos))
aprobada = (APROBADA.inicio, APROBADA.fin)
ok("ninguno pisa la clase aprobada", all(not se_pisan(h, aprobada) for h in huecos))
pendiente = (PENDIENTE.inicio, PENDIENTE.fin)
ok("la pendiente NO ocupa: hay un hueco encima", any(se_pisan(h, pendiente) for h in huecos), PENDIENTE)
bloqueo = filas("SELECT inicio, fin FROM bloqueo WHERE perfil_profesor_id = :p", p=PERFIL1)[0]
ok("ninguno pisa el bloqueo de los seeds", all(not se_pisan(h, (bloqueo.inicio, bloqueo.fin)) for h in huecos))

estado, dias90 = disponibilidad(ID["profe1"], desde, hasta, duracion=90)
huecos90 = huecos_de(dias90)
ok("con 90 minutos: duran 90 y arrancan en :00 o :30",
   estado == 200 and huecos90 and all(f - i == timedelta(minutes=90) and i.minute in (0, 30) for i, f in huecos90))

reglas(descanso_min=30)
_, dias = disponibilidad(ID["profe1"], desde, hasta)
alrededor = (APROBADA.inicio - timedelta(minutes=30), APROBADA.fin + timedelta(minutes=30))
ok("descanso de 30 min: nada en la media hora antes y despues de la aprobada",
   all(not se_pisan(h, alrededor) for h in huecos_de(dias)))
reglas(descanso_min=0)

reglas(max_clases_dia=1)
_, dias = disponibilidad(ID["profe1"], desde, hasta)
dia_aprobada = APROBADA.inicio.astimezone(fechas.ZONA).date().isoformat()
ok("tope de 1 clase por dia: el dia de la aprobada queda sin huecos",
   [d["huecos"] for d in dias if d["fecha"] == dia_aprobada] == [[]])
reglas(max_clases_dia=None)

reglas(aviso_minimo_horas=72)
_, dias = disponibilidad(ID["profe1"], desde, hasta)
ok("aviso minimo de 72 h: nada en los proximos tres dias",
   all(i >= fechas.ahora() + timedelta(hours=72) for i, _ in huecos_de(dias)))
reglas(aviso_minimo_horas=12)


# ===========================================================================
# POST /agenda/verificar
# ===========================================================================

seccion("Verificar: cada motivo")
libre = huecos[len(huecos) // 2]
estado, cuerpo = verificar(ID["profe1"], libre[0].isoformat())
ok("un hueco del calendario: libre", estado == 200 and cuerpo == {"libre": True, "motivo": None}, cuerpo)
# Un inicio que no esta alineado pero entra entero en lo libre: dos huecos seguidos.
seguidos = next(a for a, b in zip(huecos, huecos[1:]) if a[1] == b[0])  # el primero de los dos
_, cuerpo = verificar(ID["profe1"], (seguidos[0] + timedelta(minutes=15)).isoformat())
ok("14:15 adentro de lo libre: libre aunque no sea un hueco ofrecido", cuerpo.get("libre") is True, (seguidos, cuerpo))

_, cuerpo = verificar(ID["profe1"], (fechas.ahora() + timedelta(hours=2)).isoformat())
ok("dentro de dos horas: aviso_minimo", cuerpo == {"libre": False, "motivo": "aviso_minimo"}, cuerpo)
_, cuerpo = verificar(ID["profe1"], (fechas.ahora() - timedelta(days=1)).isoformat())
ok("ayer: aviso_minimo", cuerpo.get("motivo") == "aviso_minimo", cuerpo)
_, cuerpo = verificar(ID["profe1"], iso(dia_habil(5), 8))
ok("a las 8 de un dia habil: fuera_de_franja", cuerpo.get("motivo") == "fuera_de_franja", cuerpo)
_, cuerpo = verificar(ID["profe1"], iso(dia_habil(5), 19, 30))
ok("19:30 por una hora (la franja termina a las 20): fuera_de_franja", cuerpo.get("motivo") == "fuera_de_franja", cuerpo)
_, cuerpo = verificar(ID["profe1"], (bloqueo.inicio + timedelta(minutes=30)).isoformat())
ok("adentro del bloqueo: bloqueado", cuerpo.get("motivo") == "bloqueado", cuerpo)
_, cuerpo = verificar(ID["profe1"], APROBADA.inicio.isoformat())
ok("encima de la aprobada: ocupado", cuerpo.get("motivo") == "ocupado", cuerpo)
_, cuerpo = verificar(ID["profe1"], PENDIENTE.inicio.isoformat())
ok("encima de una pendiente: libre", cuerpo.get("libre") is True, cuerpo)
reglas(max_clases_dia=1)
# Una hora de la franja de profe1 (14 a 20) que no pise la aprobada.
inicio_aprobada = APROBADA.inicio.astimezone(fechas.ZONA)
otra_hora = inicio_aprobada.replace(hour=14 if inicio_aprobada.hour >= 16 else 18, minute=0)
_, cuerpo = verificar(ID["profe1"], otra_hora.isoformat())
ok("con tope 1, otra hora del dia de la aprobada: tope_diario", cuerpo.get("motivo") == "tope_diario", cuerpo)
reglas(max_clases_dia=None)
error("profesor que no existe", verificar(99999, iso(dia_habil(5), 15)), 404, "profesor_no_existe")


# ===========================================================================
# GET y PUT /agenda/yo/franjas
# ===========================================================================

seccion("Franjas")
estado, lista = pedir("GET", "/agenda/yo/franjas", token=profe1)
ok("GET: las franjas de los seeds, por dia", estado == 200 and len(lista) == len(FRANJAS_ORIGINALES)
   and [f["dia_semana"] for f in lista] == sorted(f["dia_semana"] for f in lista), lista)
error("GET sin token", pedir("GET", "/agenda/yo/franjas"), 401, "sin_token")
error("GET como alumno", pedir("GET", "/agenda/yo/franjas", token=alumno1), 403, "no_es_tuyo")
error("PUT como alumno", pedir("PUT", "/agenda/yo/franjas", {"franjas": []}, token=alumno1), 403, "no_es_tuyo")

lunes_10_12 = {"dia_semana": 1, "hora_inicio": "10:00", "hora_fin": "12:00"}
error("PUT con dos que se pisan el mismo dia", pedir("PUT", "/agenda/yo/franjas", {"franjas": [
    lunes_10_12, {"dia_semana": 1, "hora_inicio": "11:00", "hora_fin": "13:00"}]}, token=profe1),
    409, "franjas_superpuestas")
error("PUT con fin antes que inicio", pedir("PUT", "/agenda/yo/franjas", {"franjas": [
    {"dia_semana": 2, "hora_inicio": "12:00", "hora_fin": "10:00"}]}, token=profe1), 400, "franja_invalida")
estado, _ = pedir("PUT", "/agenda/yo/franjas", {"franjas": [{**lunes_10_12, "dia_semana": 7}]}, token=profe1)
ok("PUT con dia 7: 422", estado == 422, estado)
ok("los errores no tocaron nada", sql("SELECT count(*) FROM franja_disponibilidad WHERE perfil_profesor_id = :p",
                                      p=PERFIL1) == len(FRANJAS_ORIGINALES))

pegadas = {"dia_semana": 1, "hora_inicio": "12:00", "hora_fin": "13:00", "modalidad": "online"}
estado, lista = pedir("PUT", "/agenda/yo/franjas", {"franjas": [pegadas, lunes_10_12]}, token=profe1)
ok("PUT: reemplaza todo (dos pegadas no se pisan), ordenadas",
   estado == 200 and [(f["hora_inicio"], f["modalidad"]) for f in lista] == [("10:00:00", "ambas"), ("12:00:00", "online")],
   lista)
_, dias = disponibilidad(ID["profe1"], dia_habil(3), dia_habil(3) + timedelta(days=6))
inicios = {i.strftime("%a %H:%M") for i, _ in huecos_de(dias)}
ok("la disponibilidad ya refleja las nuevas: solo lunes de 10 a 13", inicios == {"Mon 10:00", "Mon 11:00", "Mon 12:00"},
   inicios)

estado, _ = pedir("PUT", "/agenda/yo/franjas", {"franjas": []}, token=profe1)
ok("PUT vacio: sin franjas", estado == 200 and sql(
    "SELECT count(*) FROM franja_disponibilidad WHERE perfil_profesor_id = :p", p=PERFIL1) == 0)
error("publicar la ficha sin franjas: ficha_incompleta",
      pedir("PUT", "/perfiles/profesor/yo/estado", {"estado_ficha": "publicada"}, token=profe1), 400, "ficha_incompleta")
_, dias = disponibilidad(ID["profe1"], desde, hasta)
ok("sin franjas: el calendario sale vacio", huecos_de(dias) == [])

estado, lista = pedir("PUT", "/agenda/yo/franjas", {"franjas": FRANJAS_ORIGINALES}, token=profe1)
ok("PUT: vuelven las de los seeds", estado == 200 and len(lista) == len(FRANJAS_ORIGINALES), lista)
estado, _ = pedir("PUT", "/perfiles/profesor/yo/estado", {"estado_ficha": "publicada"}, token=profe1)
ok("con franjas, publicar anda", estado == 200, estado)


# ===========================================================================
# /agenda/yo/bloqueos
# ===========================================================================

seccion("Bloqueos")
estado, lista = pedir("GET", "/agenda/yo/bloqueos", token=profe1)
ok("GET sin rango: el de los seeds (todavia no termino)", estado == 200 and len(lista) == 1
   and lista[0]["motivo"] == "Turno medico", lista)
error("GET como alumno", pedir("GET", "/agenda/yo/bloqueos", token=alumno1), 403, "no_es_tuyo")

def bloquear(inicio: str, fin: str, motivo="Prueba", token=profe1):
    return pedir("POST", "/agenda/yo/bloqueos", {"inicio": inicio, "fin": fin, "motivo": motivo}, token=token)

error("fin antes que inicio", bloquear(iso(dia_habil(6), 16), iso(dia_habil(6), 15)), 400, "bloqueo_invalido")
error("ya paso", bloquear((fechas.ahora() - timedelta(hours=3)).isoformat(),
                          (fechas.ahora() - timedelta(hours=2)).isoformat()), 400, "bloqueo_invalido")
error("encima de la aprobada", bloquear((APROBADA.inicio - timedelta(minutes=30)).isoformat(),
                                        (APROBADA.inicio + timedelta(minutes=30)).isoformat()), 409, "hay_clase_aprobada")

dia_libre = dia_habil(12)
estado, nuevo = bloquear(iso(dia_libre, 14), iso(dia_libre, 17), "  Dentista  ")
ok("POST: 201, con el motivo limpio", estado == 201 and nuevo["motivo"] == "Dentista", nuevo)
error("otro encima del recien creado", bloquear(iso(dia_libre, 16), iso(dia_libre, 18)), 409, "bloqueo_superpuesto")
estado, pegado = bloquear(iso(dia_libre, 17), iso(dia_libre, 18))
ok("uno pegado (17 a 18) no se pisa", estado == 201, pegado)
_, cuerpo = verificar(ID["profe1"], iso(dia_libre, 15))
ok("verificar adentro del nuevo bloqueo: bloqueado", cuerpo.get("motivo") == "bloqueado", cuerpo)
estado, lista = pedir("GET", f"/agenda/yo/bloqueos?desde={dia_libre}&hasta={dia_libre}", token=profe1)
ok("GET con rango: los dos de ese dia", estado == 200 and [b["id"] for b in lista] == [nuevo["id"], pegado["id"]], lista)

error("borrar uno ajeno", pedir("DELETE", f"/agenda/yo/bloqueos/{nuevo['id']}", token=profe2), 403, "no_es_tuyo")
error("borrar uno que no existe", pedir("DELETE", "/agenda/yo/bloqueos/99999", token=profe1), 404, "bloqueo_no_existe")
estado, _ = pedir("DELETE", f"/agenda/yo/bloqueos/{nuevo['id']}", token=profe1)
ok("DELETE: 204", estado == 204, estado)
_, cuerpo = verificar(ID["profe1"], iso(dia_libre, 15))
ok("borrado el bloqueo, ese rato vuelve a estar libre", cuerpo.get("libre") is True, cuerpo)
pedir("DELETE", f"/agenda/yo/bloqueos/{pegado['id']}", token=profe1)

estado, encima = bloquear(PENDIENTE.inicio.isoformat(), PENDIENTE.fin.isoformat(), "Encima de la pendiente")
ok("se puede bloquear encima de una PENDIENTE", estado == 201, encima)
error("y despues aprobarla: horario_ocupado (clases pregunta a agenda)",
      pedir("POST", f"/clases/{PENDIENTE.id}/aprobar", token=profe1), 409, "horario_ocupado")
pedir("DELETE", f"/agenda/yo/bloqueos/{encima['id']}", token=profe1)


# ===========================================================================
# GET /agenda/yo/semana
# ===========================================================================

seccion("Semana")
error("como alumno", pedir("GET", "/agenda/yo/semana", token=alumno1), 403, "no_es_tuyo")
desde_semana = APROBADA.inicio.astimezone(fechas.ZONA).date() - timedelta(days=1)
estado, semana = pedir("GET", f"/agenda/yo/semana?desde={desde_semana}", token=profe1)
ok("200 con desde y hasta (siete dias)", estado == 200 and semana["desde"] == desde_semana.isoformat()
   and semana["hasta"] == (desde_semana + timedelta(days=6)).isoformat(), semana)
# Con los seeds grandes profe1 tiene varias aprobadas por semana: tienen que
# venir todas las de esos siete dias, y entre ellas la del calendario.
aprobadas_semana = sorted(i for (i,) in filas(
    "SELECT id FROM clase WHERE profesor_id = :p AND estado = 'aprobada' AND inicio >= :d AND inicio < :h",
    p=ID["profe1"], d=fechas.inicio_del_dia(desde_semana), h=fechas.inicio_del_dia(desde_semana + timedelta(days=7))))
ok("trae las aprobadas de la semana, y entre ellas la del calendario",
   APROBADA.id in [c["id"] for c in semana["aprobadas"]]
   and sorted(c["id"] for c in semana["aprobadas"]) == aprobadas_semana, (semana["aprobadas"], aprobadas_semana))
ok("las filas tienen la forma de GET /clases (contraparte, total, cobro_estado)",
   all({"contraparte", "total", "cobro_estado", "materia"} <= set(c) for c in semana["aprobadas"]))
en_rango = PENDIENTE.inicio.astimezone(fechas.ZONA).date() <= desde_semana + timedelta(days=6)
ok("la pendiente aparece si cae en la semana", (PENDIENTE.id in [c["id"] for c in semana["pendientes"]]) == en_rango)
_, pasada = pedir("GET", f"/agenda/yo/semana?desde={HOY - timedelta(days=21)}", token=profe1)
dictadas = sql("SELECT count(*) FROM clase WHERE profesor_id = :p AND estado = 'dictada' AND inicio >= :d AND inicio < :h",
               p=ID["profe1"], d=fechas.inicio_del_dia(HOY - timedelta(days=21)),
               h=fechas.inicio_del_dia(HOY - timedelta(days=14)))
ok("semana pasada: las dictadas van en cerradas", len(pasada["cerradas"]) == dictadas, (pasada["cerradas"], dictadas))
ok("las canceladas no vienen en ninguna lista", all(
    c["estado"] != "cancelada" for clave in ("aprobadas", "pendientes", "cerradas") for c in pasada[clave]))
_, con_bloqueo = pedir("GET", f"/agenda/yo/semana?desde={bloqueo.inicio.astimezone(fechas.ZONA).date()}", token=profe1)
ok("los bloqueos de la semana", [b["motivo"] for b in con_bloqueo["bloqueos"]] == ["Turno medico"], con_bloqueo["bloqueos"])
estado, _ = pedir("GET", "/agenda/yo/semana", token=profe1)
ok("sin desde: arranca hoy", estado == 200, estado)


# ===========================================================================
# Lo que consumen los otros modulos
# ===========================================================================

seccion("Busqueda, clases y perfiles usando agenda")
estado, cuerpo = pedir("GET", "/busqueda/profesores")
ok("busqueda: proxima_hora_libre ya no viene en null", estado == 200 and cuerpo["resultados"]
   and all(r["proxima_hora_libre"] for r in cuerpo["resultados"]), cuerpo)
estado, manana = pedir("GET", "/busqueda/profesores?franja=manana")
de_manana = {u for (u,) in filas(
    "SELECT p.usuario_id FROM franja_disponibilidad f JOIN perfil_profesor p ON p.id = f.perfil_profesor_id "
    "WHERE f.hora_inicio < '12:00' AND p.estado_ficha = 'publicada'")}
ok("franja=manana: 200 y solo los que tienen franjas de manana",
   estado == 200 and manana["total"] > 0 and {r["id"] for r in manana["resultados"]} == de_manana,
   (manana, de_manana))
estado, domingo = pedir("GET", "/busqueda/profesores?dia=0")
ok("dia=0 (domingo, nadie atiende): ninguno", estado == 200 and domingo["total"] == 0, domingo)
# Con los seeds grandes hay profesores con la agenda llena: que tenga franja
# no alcanza para aparecer, tiene que tener un hueco libre. Por eso se pide
# que vengan algunos, y que todos los que vienen tengan esa franja.
estado, finde = pedir("GET", "/busqueda/profesores?franja=fin_de_semana")
de_finde = {u for (u,) in filas(
    "SELECT p.usuario_id FROM franja_disponibilidad f JOIN perfil_profesor p ON p.id = f.perfil_profesor_id "
    "WHERE f.dia_semana IN (0, 6) AND p.estado_ficha = 'publicada'")}
ok("franja=fin_de_semana: algunos, y solo de los que atienden sabado o domingo", estado == 200
   and finde["total"] > 0 and {r["id"] for r in finde["resultados"]} <= de_finde, (finde, de_finde))
# Un dia habil a 3 o mas dias, asi el aviso minimo no lo tapa.
dia_tarde = dia_habil(3).isoweekday() % 7
estado, martes = pedir("GET", f"/busqueda/profesores?dia={dia_tarde}&franja=tarde")
de_tarde = {u for (u,) in filas(
    "SELECT p.usuario_id FROM franja_disponibilidad f JOIN perfil_profesor p ON p.id = f.perfil_profesor_id "
    "WHERE f.dia_semana = :d AND f.hora_inicio < '18:00' AND f.hora_fin > '12:00' AND p.estado_ficha = 'publicada'",
    d=dia_tarde)}
ok("un dia habil de tarde: algunos, y solo de los que atienden esa tarde", estado == 200
   and martes["total"] > 0 and {r["id"] for r in martes["resultados"]} <= de_tarde, (martes.get("total"), de_tarde))

error("reprogramar la aprobada a las 8 (fuera de franja): horario_ocupado",
      pedir("POST", f"/clases/{APROBADA.id}/reprogramar", {"inicio": iso(dia_habil(6), 8)}, token=profe1),
      409, "horario_ocupado")
ok("el reprogramar fallido no la dejo en pendiente",
   sql("SELECT estado::text FROM clase WHERE id = :c", c=APROBADA.id) == "aprobada")

from app.modulos.agenda import logica as agenda  # noqa: E402

with SesionLocal() as db:
    publicados = [u for (u,) in db.execute(text(
        "SELECT usuario_id FROM perfil_profesor WHERE estado_ficha = 'publicada' ORDER BY usuario_id"))]
    al_reves = list(reversed(publicados))
    con_tarde = agenda.filtrar_con_hueco(db, al_reves, None, "tarde")
    ok("filtrar_con_hueco: respeta el orden recibido (y deja afuera a los que no tienen tarde libre)",
       con_tarde and con_tarde == [u for u in al_reves if u in con_tarde], con_tarde)
    ok("filtrar_con_hueco: lista vacia -> vacia", agenda.filtrar_con_hueco(db, [], 2, None) == [])
    primeras = agenda.primera_hora_libre(db, publicados + [ID["alumno1"]])
    ok("primera_hora_libre: uno por profesor, el alumno no", set(primeras) == set(publicados), primeras)
    ok("tiene_franjas", agenda.tiene_franjas(db, PERFIL1))
    ok("hay_bloqueo_encima", agenda.hay_bloqueo_encima(db, PERFIL1, bloqueo.inicio, bloqueo.fin)
       and not agenda.hay_bloqueo_encima(db, PERFIL1, bloqueo.fin, bloqueo.fin + timedelta(hours=1)))


# ===========================================================================
# RESENAS - POST y PUT /resenas, GET /resenas/resumen y /usuario
# ===========================================================================

def puntaje_en_perfil(usuario_id: int):
    """(promedio, cantidad) desnormalizados en el perfil, sea profesor o alumno."""
    fila = filas("SELECT puntaje_promedio, cantidad_resenas FROM perfil_profesor WHERE usuario_id = :u "
                 "UNION ALL SELECT puntaje_promedio, cantidad_resenas FROM perfil_estudiante WHERE usuario_id = :u",
                 u=usuario_id)[0]
    return float(fila[0]), fila[1]


def en_tabla(usuario_id: int):
    """(promedio, cantidad) calculados en vivo sobre la tabla resena."""
    fila = filas("SELECT coalesce(round(avg(puntaje), 2), 0), count(*) FROM resena WHERE destinatario_id = :u",
                 u=usuario_id)[0]
    return float(fila[0]), fila[1]


seccion("Resenas: dejar y editar")
# Un par (alumno, profe) con clase dictada y SIN resena del alumno todavia.
sin_resena = filas(
    "SELECT DISTINCT c.estudiante_id, c.profesor_id FROM clase c WHERE c.estado = 'dictada' AND NOT EXISTS "
    "(SELECT 1 FROM resena r WHERE r.autor_id = c.estudiante_id AND r.destinatario_id = c.profesor_id) "
    "ORDER BY 1, 2 LIMIT 1")[0]
alumno_id, profe_id = sin_resena.estudiante_id, sin_resena.profesor_id
token_alumno = login(sql("SELECT correo FROM usuario WHERE id = :u", u=alumno_id))
nunca = sql("SELECT id FROM usuario WHERE rol = 'profesor' AND id NOT IN "
            "(SELECT profesor_id FROM clase WHERE estudiante_id = :a AND estado = 'dictada') LIMIT 1", a=alumno_id)
HOY_ISO = fechas.ahora().date().isoformat()

error("a alguien con quien nunca tuvo clase dictada",
      pedir("POST", "/resenas", {"destinatario_id": nunca, "puntaje": 5}, token=token_alumno),
      403, "sin_clases_con_esa_persona")
error("PUT sin haber dejado ninguna", pedir("PUT", "/resenas", {"destinatario_id": profe_id, "puntaje": 4},
                                           token=token_alumno), 404, "resena_no_existe")
for malo in (0, 6):
    estado, _ = pedir("POST", "/resenas", {"destinatario_id": profe_id, "puntaje": malo}, token=token_alumno)
    ok(f"puntaje {malo}: 422", estado == 422, estado)
estado, _ = pedir("POST", "/resenas", {"destinatario_id": profe_id, "puntaje": 4, "texto": "x" * 501}, token=token_alumno)
ok("texto de mas de 500: 422", estado == 422, estado)
error("sin token", pedir("POST", "/resenas", {"destinatario_id": profe_id, "puntaje": 4}), 401, "sin_token")

antes = puntaje_en_perfil(profe_id)
estado, creada = pedir("POST", "/resenas", {"destinatario_id": profe_id, "puntaje": 2, "texto": "  Llego tarde  "},
                       token=token_alumno)
ok("POST: 201, texto limpio, fecha de hoy",
   estado == 201 and creada == {"puntaje": 2, "texto": "Llego tarde", "fecha": HOY_ISO}, creada)
ok("POST: el sentido sale del rol (alumno_a_profesor)", sql(
    "SELECT sentido::text FROM resena WHERE autor_id = :a AND destinatario_id = :p", a=alumno_id, p=profe_id)
   == "alumno_a_profesor")
ok("POST: el perfil del profe se recalculo", puntaje_en_perfil(profe_id) == en_tabla(profe_id)
   and puntaje_en_perfil(profe_id)[1] == antes[1] + 1, (antes, puntaje_en_perfil(profe_id)))
error("POST otra vez", pedir("POST", "/resenas", {"destinatario_id": profe_id, "puntaje": 5}, token=token_alumno),
      409, "ya_resenado")
estado, editada = pedir("PUT", "/resenas", {"destinatario_id": profe_id, "puntaje": 5, "texto": ""}, token=token_alumno)
ok("PUT: cambia puntaje, texto vacio queda en null",
   estado == 200 and editada["puntaje"] == 5 and editada["texto"] is None, editada)
ok("PUT: el promedio se recalculo y la cantidad no cambio", puntaje_en_perfil(profe_id) == en_tabla(profe_id)
   and puntaje_en_perfil(profe_id)[1] == antes[1] + 1)
_, mis = pedir("GET", "/clases/mis-profesores", token=token_alumno)
ok("mis-profesores: mi_resena ya viene llena", [m["mi_resena"] for m in mis if m["persona"]["id"] == profe_id]
   == [{"puntaje": 5, "texto": None, "fecha": HOY_ISO}], mis)

seccion("Resenas: del profesor al alumno")
par = filas(
    "SELECT DISTINCT c.estudiante_id, c.profesor_id FROM clase c WHERE c.estado = 'dictada' AND NOT EXISTS "
    "(SELECT 1 FROM resena r WHERE r.autor_id = c.profesor_id AND r.destinatario_id = c.estudiante_id) "
    "ORDER BY 2, 1 LIMIT 1")[0]
token_profe = login(sql("SELECT correo FROM usuario WHERE id = :u", u=par.profesor_id))
estado, _ = pedir("POST", "/resenas", {"destinatario_id": par.estudiante_id, "puntaje": 4, "texto": "Muy aplicada"},
                  token=token_profe)
ok("POST del profe: 201 y sentido profesor_a_alumno", estado == 201 and sql(
    "SELECT sentido::text FROM resena WHERE autor_id = :p AND destinatario_id = :a",
    p=par.profesor_id, a=par.estudiante_id) == "profesor_a_alumno")
ok("el perfil del ALUMNO se recalculo", puntaje_en_perfil(par.estudiante_id) == en_tabla(par.estudiante_id))
_, alumnos = pedir("GET", "/clases/mis-alumnos", token=token_profe)
ok("mis-alumnos: mi_resena llena", any(a["persona"]["id"] == par.estudiante_id and a["mi_resena"]
                                       and a["mi_resena"]["puntaje"] == 4 for a in alumnos), alumnos)
_, yo = pedir("GET", "/usuarios/yo", token=login(sql("SELECT correo FROM usuario WHERE id = :u", u=par.estudiante_id)))
ok("GET /usuarios/yo del alumno: su puntaje en la cabecera",
   (yo["estudiante"]["puntaje_promedio"], yo["estudiante"]["cantidad_resenas"]) == en_tabla(par.estudiante_id), yo)

seccion("Resenas: leer")
estado, resumen = pedir("GET", f"/resenas/resumen/{profe_id}")
ok("resumen: las cinco estrellas siempre, de 5 a 1",
   estado == 200 and list(resumen["distribucion"]) == ["5", "4", "3", "2", "1"], resumen)
ok("resumen: total y promedio = la tabla", (resumen["promedio"], resumen["total"]) == en_tabla(profe_id), resumen)
ok("resumen: la distribucion suma el total", sum(resumen["distribucion"].values()) == resumen["total"])
_, vacio = pedir("GET", f"/resenas/resumen/{ID['profe7']}")
ok("resumen sin resenas: ceros",
   vacio == {"total": 0, "promedio": 0.0, "distribucion": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}}, vacio)
error("resumen de alguien que no existe", pedir("GET", "/resenas/resumen/99999"), 404, "usuario_no_existe")
error("orden invalido", pedir("GET", f"/resenas/usuario/{profe_id}?orden=autor"), 400, "orden_invalido")
estado, _ = pedir("GET", f"/resenas/usuario/{profe_id}?pagina=0")
ok("pagina 0: 422", estado == 422, estado)

_, por_puntaje = pedir("GET", f"/resenas/usuario/{profe_id}?orden=puntaje")
puntajes = [r["puntaje"] for r in por_puntaje["resenas"]]
ok("orden=puntaje: de mayor a menor",
   puntajes == sorted(puntajes, reverse=True) and len(puntajes) == resumen["total"], puntajes)
_, recientes = pedir("GET", f"/resenas/usuario/{profe_id}")
ok("orden=recientes: la mas nueva primero", recientes["resenas"][0]["fecha"] == HOY_ISO, recientes["resenas"][:1])

# El anonimato: ni el id ni el nombre del autor en ninguna respuesta publica.
nombre_autor = sql("SELECT nombre FROM usuario WHERE id = :u", u=alumno_id)
crudo = json.dumps([resumen, por_puntaje, recientes])
ok("anonimas: ninguna respuesta trae autor ni el nombre de quien escribio",
   "autor" not in crudo and nombre_autor not in crudo, crudo[:200])
ok("anonimas: cada resena es solo puntaje, texto y fecha",
   all(set(r) == {"puntaje", "texto", "fecha"} for r in por_puntaje["resenas"]))

# Pagina 2: once resenas mas para profe2, insertadas directo (con los seeds no
# hay tantos alumnos con clase dictada como para armarlo por la API).
mucho = ID["profe2"]
otros = [u for (u,) in filas("SELECT id FROM usuario WHERE rol = 'estudiante' AND id NOT IN "
                              "(SELECT autor_id FROM resena WHERE destinatario_id = :p) ORDER BY id LIMIT 11", p=mucho)]
for u in otros:
    ejecutar("INSERT INTO resena (autor_id, destinatario_id, sentido, puntaje) "
             "VALUES (:a, :p, 'alumno_a_profesor', 3)", a=u, p=mucho)
_, p1 = pedir("GET", f"/resenas/usuario/{mucho}")
_, p2 = pedir("GET", f"/resenas/usuario/{mucho}?pagina=2")
ok("paginas de a 10: la 1 trae 10 y la 2 el resto", len(p1["resenas"]) == 10
   and len(p2["resenas"]) == p1["total"] - 10 and p1["total"] == p2["total"], (p1["total"], len(p2["resenas"])))


# ===========================================================================
# MENSAJERIA - /mensajes/no-leidos, /hilos y /hilos/{id}/mensajes
# ===========================================================================

def no_leidos(token: str) -> int:
    return pedir("GET", "/mensajes/no-leidos", token=token)[1]["no_leidos"]


seccion("Mensajeria: abrir hilos")
alumno3 = login("alumno3@example.com")
error("sin token", pedir("GET", "/mensajes/no-leidos"), 401, "sin_token")
error("alumno sin profesor_id", pedir("POST", "/mensajes/hilos", {"estudiante_id": ID["alumno2"]}, token=alumno3),
      400, "datos_invalidos")
error("alumno con el id de otro alumno", pedir("POST", "/mensajes/hilos", {"profesor_id": ID["alumno2"]}, token=alumno3),
      404, "profesor_no_existe")
assert sql("SELECT count(*) FROM hilo WHERE estudiante_id = :a AND profesor_id = :p",
           a=ID["alumno3"], p=ID["profe1"]) == 0
estado, nuevo_hilo = pedir("POST", "/mensajes/hilos", {"profesor_id": ID["profe1"]}, token=alumno3)
ok("alumno abre un hilo nuevo: 201, contraparte con materias, sin mensajes",
   estado == 201 and nuevo_hilo["contraparte"]["id"] == ID["profe1"] and nuevo_hilo["contraparte"]["materias"]
   and nuevo_hilo["ultimo_mensaje"] is None and nuevo_hilo["no_leidos"] == 0, nuevo_hilo)
estado, otra_vez = pedir("POST", "/mensajes/hilos", {"profesor_id": ID["profe1"]}, token=alumno3)
ok("abrirlo otra vez: 200 y el MISMO hilo", estado == 200 and otra_vez["id"] == nuevo_hilo["id"], (estado, otra_vez))

sin_clase = sql("SELECT id FROM usuario WHERE rol = 'estudiante' AND id NOT IN "
                "(SELECT estudiante_id FROM clase WHERE profesor_id = :p) ORDER BY id LIMIT 1", p=ID["profe1"])
error("profe con un alumno sin ninguna clase", pedir("POST", "/mensajes/hilos", {"estudiante_id": sin_clase},
                                                     token=profe1), 403, "sin_clases_con_esa_persona")
error("profe sin estudiante_id", pedir("POST", "/mensajes/hilos", {"profesor_id": ID["profe2"]}, token=profe1),
      400, "datos_invalidos")
con_clase = sql("SELECT estudiante_id FROM clase WHERE profesor_id = :p AND estudiante_id NOT IN "
                "(SELECT estudiante_id FROM hilo WHERE profesor_id = :p) ORDER BY estudiante_id LIMIT 1", p=ID["profe1"])
estado, del_profe = pedir("POST", "/mensajes/hilos", {"estudiante_id": con_clase}, token=profe1)
ok("profe con un alumno con clase: 201, contraparte con etapa y sin materias",
   estado == 201 and del_profe["contraparte"]["id"] == con_clase and del_profe["contraparte"]["materias"] == []
   and del_profe["contraparte"]["rol"] == "estudiante", del_profe)

seccion("Mensajeria: enviar y leer")
error("mensaje vacio", pedir("POST", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", {"texto": "   "}, token=alumno3),
      400, "mensaje_vacio")
estado, _ = pedir("POST", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", {"texto": "x" * 2001}, token=alumno3)
ok("mensaje de mas de 2000: 422", estado == 422, estado)
error("escribir en un hilo ajeno", pedir("POST", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", {"texto": "hola"},
                                         token=alumno1), 403, "no_es_tuyo")
error("leer un hilo ajeno", pedir("GET", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", token=alumno1),
      403, "no_es_tuyo")
error("hilo que no existe", pedir("GET", "/mensajes/hilos/99999/mensajes", token=alumno1), 404, "hilo_no_existe")

antes_profe, antes_alumno = no_leidos(profe1), no_leidos(alumno3)
estado, enviado = pedir("POST", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", {"texto": "  Hola! Tenes lugar el martes?  "},
                        token=alumno3)
pedir("POST", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", {"texto": "Es para matematica."}, token=alumno3)
ok("enviar: 201, texto limpio, autor = quien envia", estado == 201 and enviado["contenido"] == "Hola! Tenes lugar el martes?"
   and enviado["autor_id"] == ID["alumno3"], enviado)
ok("el contador sube para el que recibe (y no para el que envia)",
   no_leidos(profe1) == antes_profe + 2 and no_leidos(alumno3) == antes_alumno, (no_leidos(profe1), antes_profe))
_, yo_profe = pedir("GET", "/usuarios/yo", token=profe1)
ok("GET /usuarios/yo trae el mismo contador", yo_profe["mensajes_no_leidos"] == no_leidos(profe1), yo_profe)
_, bandeja = pedir("GET", "/mensajes/hilos", token=profe1)
ok("bandeja del profe: el hilo recien escrito queda primero, con 2 sin leer y el ultimo mensaje",
   bandeja[0]["id"] == nuevo_hilo["id"] and bandeja[0]["no_leidos"] == 2
   and bandeja[0]["ultimo_mensaje"] == "Es para matematica.", bandeja[:1])
ok("bandeja: ordenada por actividad (sin mensajes al final)",
   [h["ultimo_mensaje_el"] is None for h in bandeja] == sorted(h["ultimo_mensaje_el"] is None for h in bandeja)
   and [h["ultimo_mensaje_el"] for h in bandeja if h["ultimo_mensaje_el"]]
   == sorted((h["ultimo_mensaje_el"] for h in bandeja if h["ultimo_mensaje_el"]), reverse=True))

estado, leidos = pedir("GET", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", token=profe1)
ok("abrir el hilo: los mensajes en orden cronologico", estado == 200
   and [m["contenido"] for m in leidos] == ["Hola! Tenes lugar el martes?", "Es para matematica."], leidos)
ok("abrir el hilo los marca como leidos: el contador baja", no_leidos(profe1) == antes_profe, no_leidos(profe1))
ok("en la base: leido_el puesto en los del alumno", sql(
    "SELECT count(*) FROM mensaje WHERE hilo_id = :h AND leido_el IS NULL", h=nuevo_hilo["id"]) == 0)
pedir("POST", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", {"texto": "Si, a las 16."}, token=profe1)
pedir("GET", f"/mensajes/hilos/{nuevo_hilo['id']}/mensajes", token=profe1)
ok("el que abre NO marca sus propios mensajes como leidos", sql(
    "SELECT count(*) FROM mensaje WHERE hilo_id = :h AND leido_el IS NULL AND autor_id = :p",
    h=nuevo_hilo["id"], p=ID["profe1"]) == 1)

seccion("Mensajeria: historial y busqueda")
largo = sql("SELECT hilo_id FROM mensaje GROUP BY hilo_id HAVING count(*) >= 6 ORDER BY hilo_id LIMIT 1")
token_largo = login(sql("SELECT u.correo FROM hilo h JOIN usuario u ON u.id = h.estudiante_id WHERE h.id = :h", h=largo))
total_largo = sql("SELECT count(*) FROM mensaje WHERE hilo_id = :h", h=largo)
_, ultimos = pedir("GET", f"/mensajes/hilos/{largo}/mensajes?limite=4", token=token_largo)
_, anteriores = pedir("GET", f"/mensajes/hilos/{largo}/mensajes?limite=4&antes={ultimos[0]['id']}", token=token_largo)
ok("limite=4: los 4 mas nuevos, en orden", len(ultimos) == 4
   and [m["enviado_el"] for m in ultimos] == sorted(m["enviado_el"] for m in ultimos), ultimos)
# Con los seeds grandes el hilo puede tener mas de 8: la segunda pagina trae
# otros 4, o los que queden si son menos.
ok("antes=: los anteriores, sin repetir ninguno", len(anteriores) == min(4, total_largo - 4)
   and not {m["id"] for m in anteriores} & {m["id"] for m in ultimos}
   and anteriores[-1]["enviado_el"] <= ultimos[0]["enviado_el"], anteriores)
estado, _ = pedir("GET", f"/mensajes/hilos/{largo}/mensajes?limite=101", token=token_largo)
ok("limite de mas de 100: 422", estado == 422, estado)

# Con tilde y en mayusculas, codificado en la URL como lo manda el navegador.
_, con_q = pedir("GET", f"/mensajes/hilos?q={urllib.parse.quote('LUCÍA')}", token=alumno1)
ok("q sin importar mayusculas ni tildes", con_q and all(h["contraparte"]["nombre"] == "Lucia" for h in con_q), con_q)
_, nada = pedir("GET", "/mensajes/hilos?q=zzzz", token=alumno1)
ok("q sin coincidencias: vacio", nada == [], nada)

from sqlalchemy import event  # noqa: E402

from app.modulos.mensajeria import logica as mensajeria  # noqa: E402

with SesionLocal() as db:
    consultas = []
    event.listen(db.get_bind(), "before_cursor_execute", lambda *a: consultas.append(1))
    con_muchos = sql("SELECT profesor_id FROM hilo GROUP BY 1 ORDER BY count(*) DESC LIMIT 1")
    # Los dos profesores: la contraparte es del mismo tipo (alumnos) y se arma igual.
    con_uno = sql("SELECT profesor_id FROM hilo GROUP BY 1 ORDER BY count(*), 1 LIMIT 1")
    consultas.clear()
    hilos_muchos = mensajeria.bandeja(db, con_muchos)
    cuantas_muchos = len(consultas)
    consultas.clear()
    mensajeria.bandeja(db, con_uno)
    ok("bandeja sin N+1: las mismas consultas con 1 hilo que con varios",
       len(hilos_muchos) > 1 and len(consultas) == cuantas_muchos, (len(hilos_muchos), cuantas_muchos, len(consultas)))


# ===========================================================================
# SISTEMA - la app importa y los seeds cuadran
# ===========================================================================

def correr(*argumentos: str) -> subprocess.CompletedProcess:
    """python <argumentos>, con el mismo interprete y desde backend/."""
    return subprocess.run([sys.executable, *argumentos], capture_output=True, text=True)


seccion("La app y los seeds")
r = correr("-c", "from app.main import app; print(len(app.routes))")
ok("python -c 'from app.main import app'", r.returncode == 0, r.stderr[-400:])
r = correr("-c", "import app.modulos.agenda.logica")
ok("agenda se puede importar primero (sin importacion circular)", r.returncode == 0, r.stderr[-400:])
primera, segunda = correr("-m", "app.seeds"), correr("-m", "app.seeds")
ok("seeds dos veces seguidas", primera.returncode == 0 and segunda.returncode == 0, (primera.stderr + segunda.stderr)[-400:])
ok("seeds: los promedios de todos los perfiles cuadran con la tabla resena", sql(
    "SELECT count(*) FROM (SELECT usuario_id, puntaje_promedio, cantidad_resenas FROM perfil_profesor UNION ALL "
    "SELECT usuario_id, puntaje_promedio, cantidad_resenas FROM perfil_estudiante) p LEFT JOIN "
    "(SELECT destinatario_id, round(avg(puntaje), 2) AS prom, count(*) AS n FROM resena GROUP BY 1) r "
    "ON r.destinatario_id = p.usuario_id "
    "WHERE p.puntaje_promedio <> coalesce(r.prom, 0) OR p.cantidad_resenas <> coalesce(r.n, 0)") == 0)
ok("seeds: resenas en los dos sentidos, todas sobre pares con clase dictada",
   sql("SELECT count(DISTINCT sentido) FROM resena") == 2 and sql(
       "SELECT count(*) FROM resena r WHERE NOT EXISTS (SELECT 1 FROM clase c WHERE c.estado = 'dictada' AND "
       "((c.estudiante_id = r.autor_id AND c.profesor_id = r.destinatario_id) OR "
       "(c.profesor_id = r.autor_id AND c.estudiante_id = r.destinatario_id)))") == 0)
# Los seeds cargan cientos de hilos: alcanza con que haya y que todos cuadren.
ok("seeds: cada hilo tiene ultimo_mensaje_el = su ultimo mensaje", sql(
    "SELECT count(*) FROM hilo h WHERE h.ultimo_mensaje_el IS DISTINCT FROM "
    "(SELECT max(enviado_el) FROM mensaje m WHERE m.hilo_id = h.id)") == 0
   and sql("SELECT count(*) FROM hilo") > 0)
ok("seeds: en cada hilo, el orden por id es el orden por hora (el historial pagina por id)", sql(
    "SELECT count(*) FROM (SELECT enviado_el < lag(enviado_el) OVER (PARTITION BY hilo_id ORDER BY id) AS mal "
    "FROM mensaje) x WHERE mal") == 0)
# Los seeds cargan bloqueos para muchos profesores; los fijos de P3 son los
# tres de profe1, profe2 y profe3.
ok("seeds: los 3 bloqueos de profe1 a profe3, y ningun bloqueo encima de una aprobada",
   sql("SELECT count(*) FROM bloqueo b JOIN perfil_profesor p ON p.id = b.perfil_profesor_id "
       "JOIN usuario u ON u.id = p.usuario_id "
       "WHERE u.correo IN ('profe1@example.com', 'profe2@example.com', 'profe3@example.com')") == 3 and sql(
       "SELECT count(*) FROM bloqueo b JOIN perfil_profesor p ON p.id = b.perfil_profesor_id "
       "JOIN clase c ON c.profesor_id = p.usuario_id AND c.estado = 'aprobada' "
       "AND c.inicio < b.fin AND c.fin > b.inicio") == 0)


# ===========================================================================
# Resultado
# ===========================================================================

print(f"\n{pasaron} de {pasaron + len(fallaron)} comprobaciones pasaron.")
if fallaron:
    print("Fallaron:")
    for f in fallaron:
        print("  -", f)
    sys.exit(1)
