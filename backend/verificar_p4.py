"""Comprobaciones de P4 (clases y pagos) contra un backend levantado.

Se corre desde backend/, con el venv, contra una base de PRUEBA recien
sembrada (alembic upgrade head + python -m app.seeds) y un uvicorn levantado
contra esa misma base:

    python verificar_p4.py                          # contra http://127.0.0.1:8001
    python verificar_p4.py http://127.0.0.1:8000

Recorre todos los endpoints de P4 con los usuarios de los seeds: los flujos
de la plata de punta a punta, los errores de cada uno (roles cruzados, ids
que no existen, estados invalidos) y que los importes cuadren al centesimo.
Al final baja y sube la migracion y vuelve a cargar los seeds, asi que deja
la base como recien sembrada.

OJO: ensucia la base (crea, aprueba, cancela y rechaza clases, agrega
tarjetas, cambia el precio de profe4) y despues la vuelve a sembrar. Por eso
se niega a correr si el .env apunta a la base "exonero" (la de todos los
dias), salvo con --forzar. Usar una aparte: exonero_p4, por ejemplo.

Ademas de la API, importa app/ para dos cosas que no tienen ruta: mirar la
base (el estado de un cobro, clases_dictadas) y llamar a las funciones que
consumen los otros modulos (clases_entre, tuvieron_clase, ...). Por eso se
corre desde backend/ (o con PYTHONPATH apuntando ahi).
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import text

from app import fechas
from app.config import ajustes
from app.db import SesionLocal

if ajustes.BASE_URL.rsplit("/", 1)[-1] == "exonero" and "--forzar" not in sys.argv:
    sys.exit("El .env apunta a la base 'exonero'. Esto la ensucia y la vuelve a sembrar: "
             "correlo contra una base de prueba (por ejemplo exonero_p4), o con --forzar.")

# 127.0.0.1 y no localhost: en Windows, "localhost" prueba primero IPv6 (::1),
# uvicorn escucha solo en IPv4, y cada llamada pierde dos segundos esperando.
_URLS = [a for a in sys.argv[1:] if not a.startswith("--")]
BASE = (_URLS[0] if _URLS else "http://127.0.0.1:8001").rstrip("/") + "/api"
CLAVE = "exonero123"

pasaron = 0
fallaron: list[str] = []


# ---------------------------------------------------------------------------
# Herramientas
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
    """La primera columna de la primera fila (o None). Hace commit: sirve para INSERT."""
    with SesionLocal() as db:
        valor = db.execute(text(consulta), parametros).scalar()
        db.commit()
        return valor


def login(correo: str) -> str:
    estado, cuerpo = pedir("POST", "/auth/login", {"correo": correo, "clave": CLAVE})
    assert estado == 200, (correo, estado, cuerpo)
    return cuerpo["token"]


def esperado(precio, minutos, traslado, comision=Decimal("10"), iva=Decimal("22")) -> dict:
    """El desglose calculado aca, a mano y por separado, para comparar."""
    c = lambda v: Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # noqa: E731
    subtotal = c(Decimal(precio) * minutos / 60)
    com = c((subtotal + Decimal(traslado)) * comision / 100)
    imp = c((subtotal + Decimal(traslado) + com) * iva / 100)
    return {"subtotal": subtotal, "comision": com, "impuesto": imp,
            "total": subtotal + c(traslado) + com + imp}


def futuro(dias: int, hora: int, minuto: int = 0) -> str:
    """Un dia habil dentro de `dias` dias, a esa hora de Montevideo, en ISO con zona."""
    dia = fechas.ahora().date() + timedelta(days=dias)
    while dia.weekday() >= 5:
        dia += timedelta(days=1)
    return datetime.combine(dia, datetime.min.time().replace(hour=hora, minute=minuto),
                            fechas.ZONA).isoformat()


def cantidad_clases() -> int:
    return sql("SELECT count(*) FROM clase")


def seccion(titulo: str):
    print(f"\n== {titulo}")


# ---------------------------------------------------------------------------
# Usuarios de los seeds
# ---------------------------------------------------------------------------

alumno1 = login("alumno1@example.com")
alumno2 = login("alumno2@example.com")
profe1 = login("profe1@example.com")
profe2 = login("profe2@example.com")
profe4 = login("profe4@example.com")
ID = {c: sql("SELECT id FROM usuario WHERE correo = :c", c=f"{c}@example.com")
      for c in ("alumno1", "alumno2", "alumno3", "profe1", "profe2", "profe3", "profe4",
                "profe6", "profe7", "profe8")}


# ===========================================================================
# BLOQUE A - tarjetas, historial, cotizar y crear
# ===========================================================================

seccion("Tarjetas")
estado, tarjetas = pedir("GET", "/pagos/tarjetas", token=alumno1)
ok("GET tarjetas 200", estado == 200 and isinstance(tarjetas, list) and len(tarjetas) == 1, tarjetas)
t = tarjetas[0]
ok("GET tarjetas: forma segura", set(t) == {"id", "marca", "ultimos4", "titular", "vence"}, t)
ok("GET tarjetas: sin numero completo en el JSON", "4111111111111111" not in json.dumps(tarjetas), tarjetas)
ok("GET tarjetas: ultimos4, marca y vence MM/AA",
   t["ultimos4"] == "1111" and t["marca"] == "Visa" and len(t["vence"]) == 5 and t["vence"][2] == "/", t)
TARJETA_A1 = t["id"]
TARJETA_A2 = pedir("GET", "/pagos/tarjetas", token=alumno2)[1][0]["id"]
error("GET tarjetas como profesor", pedir("GET", "/pagos/tarjetas", token=profe1), 403, "no_es_tuyo")
error("GET tarjetas sin token", pedir("GET", "/pagos/tarjetas"), 401, "sin_token")

anio = fechas.ahora().year + 2
nueva = {"numero": "4000 0000 0000 0000", "titular": "Mateo Lopez", "vence_mes": 6, "vence_anio": anio, "ccv": "321"}
estado, t0000 = pedir("POST", "/pagos/tarjetas", nueva, token=alumno1)
ok("POST tarjeta con espacios 201", estado == 201 and t0000["ultimos4"] == "0000" and t0000["marca"] == "Visa", t0000)
ok("POST tarjeta: la respuesta no trae numero ni ccv", set(t0000) == {"id", "marca", "ultimos4", "titular", "vence"}, t0000)
ok("POST tarjeta: vence MM/AA", t0000["vence"] == f"06/{anio % 100:02d}", t0000)
ok("POST tarjeta: se guarda sin espacios", sql("SELECT numero FROM tarjeta WHERE id = :i", i=t0000["id"]) == "4000000000000000")
TARJETA_0000 = t0000["id"]
estado, mc = pedir("POST", "/pagos/tarjetas", {**nueva, "numero": "5555555555554444"}, token=alumno1)
ok("POST tarjeta Mastercard", estado == 201 and mc["marca"] == "Mastercard", mc)
estado, otra = pedir("POST", "/pagos/tarjetas", {**nueva, "numero": "3782 822463 10005"}, token=alumno1)
ok("POST tarjeta Otra", estado == 201 and otra["marca"] == "Otra", otra)
error("POST tarjeta con guiones", pedir("POST", "/pagos/tarjetas", {**nueva, "numero": "4111-1111-1111-1111"}, token=alumno1), 400, "tarjeta_invalida")
error("POST tarjeta ccv con letras", pedir("POST", "/pagos/tarjetas", {**nueva, "ccv": "12a"}, token=alumno1), 400, "tarjeta_invalida")
error("POST tarjeta anio de dos cifras", pedir("POST", "/pagos/tarjetas", {**nueva, "vence_anio": 28}, token=alumno1), 400, "tarjeta_invalida")
error("POST tarjeta vencida", pedir("POST", "/pagos/tarjetas", {**nueva, "numero": "4111111111111111", "vence_mes": 1, "vence_anio": 2020}, token=alumno1), 402, "tarjeta_vencida")
error("POST tarjeta como profesor", pedir("POST", "/pagos/tarjetas", nueva, token=profe1), 403, "no_es_tuyo")

error("DELETE tarjeta de otro alumno", pedir("DELETE", f"/pagos/tarjetas/{TARJETA_A2}", token=alumno1), 403, "no_es_tuyo")
error("DELETE tarjeta inexistente", pedir("DELETE", "/pagos/tarjetas/99999", token=alumno1), 404, "tarjeta_no_existe")
estado, _ = pedir("DELETE", f"/pagos/tarjetas/{otra['id']}", token=alumno1)
ok("DELETE tarjeta propia 204", estado == 204, estado)
ok("DELETE es baja logica (la fila sigue)", sql("SELECT activa FROM tarjeta WHERE id = :i", i=otra["id"]) is False)
error("DELETE tarjeta ya dada de baja", pedir("DELETE", f"/pagos/tarjetas/{otra['id']}", token=alumno1), 404, "tarjeta_no_existe")
ids = [x["id"] for x in pedir("GET", "/pagos/tarjetas", token=alumno1)[1]]
ok("GET tarjetas no lista la dada de baja", otra["id"] not in ids and TARJETA_0000 in ids, ids)

# Una vencida que ya estaba guardada (por la API no se puede guardar).
TARJETA_VENCIDA = sql(
    "INSERT INTO tarjeta (usuario_id, numero, titular, vence_mes, vence_anio, ccv, activa) "
    "VALUES (:u, '4111111111111111', 'VENCIDA', 1, 2020, '123', true) RETURNING id", u=ID["alumno1"])


seccion("Cotizar")
lucia_presencial = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe1"], "duracion_min": 60, "modalidad": "presencial"})
ok("cotizar sin token 200", lucia_presencial[0] == 200, lucia_presencial)
c = lucia_presencial[1]
ok("cotizar: forma de CotizacionOut",
   set(c) == {"precio_hora", "horas", "subtotal", "costo_traslado", "pct_comision", "comision", "pct_iva", "impuesto", "total"}, c)
ok("cotizar: importes como texto con dos decimales", c["total"] == "1207.80" and c["horas"] == "1.00" and c["pct_iva"] == "22.00", c)
c = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe1"], "duracion_min": 90, "modalidad": "online"})[1]
ok("cotizar online 90 min", c["subtotal"] == "1200.00" and c["comision"] == "120.00" and c["total"] == "1610.40", c)
c = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe2"], "duracion_min": 60, "modalidad": "presencial", "con_traslado": True})[1]
ok("cotizar con traslado (a domicilio)", c["costo_traslado"] == "150.00" and c["total"] == "1342.00", c)
c = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe2"], "duracion_min": 60, "modalidad": "presencial", "con_traslado": False})[1]
ok("cotizar sin traslado", c["costo_traslado"] == "0.00" and c["total"] == "1140.70", c)
c = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe1"], "duracion_min": 60, "modalidad": "presencial", "con_traslado": True})[1]
ok("cotizar: traslado ignorado si el profe no se traslada", c["costo_traslado"] == "0.00", c)
c = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe6"], "duracion_min": 60, "modalidad": "online", "con_traslado": True})[1]
ok("cotizar: traslado ignorado en online", c["costo_traslado"] == "0.00", c)
error("cotizar modalidad ambas", pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe1"], "duracion_min": 60, "modalidad": "ambas"}), 400, "modalidad_invalida")
error("cotizar duracion que no ofrece", pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe1"], "duracion_min": 45, "modalidad": "presencial"}), 400, "duracion_invalida")
error("cotizar 120 min a quien ofrece hasta 90", pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe2"], "duracion_min": 120, "modalidad": "presencial"}), 400, "duracion_invalida")
error("cotizar sin precio (solo online)", pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe3"], "duracion_min": 60, "modalidad": "presencial"}), 400, "sin_precio")
error("cotizar ficha en borrador", pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe7"], "duracion_min": 60, "modalidad": "online"}), 404, "profesor_no_existe")
error("cotizar ficha pausada", pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe8"], "duracion_min": 60, "modalidad": "presencial"}), 404, "profesor_no_existe")
error("cotizar a un alumno", pedir("POST", "/clases/cotizar", {"profesor_id": ID["alumno1"], "duracion_min": 60, "modalidad": "presencial"}), 404, "profesor_no_existe")
error("cotizar id inexistente", pedir("POST", "/clases/cotizar", {"profesor_id": 99999, "duracion_min": 60, "modalidad": "presencial"}), 404, "profesor_no_existe")

# Un precio con centavos, para ver que cuadre al centesimo.
estado, _ = pedir("PUT", "/perfiles/profesor/yo/precios",
                  {"precio_hora_presencial": 873.45, "precio_hora_online": 1000}, token=profe4)
ok("profe4 cambia su precio a 873.45", estado == 200, estado)
cot = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe4"], "duracion_min": 90, "modalidad": "presencial"})[1]
e = esperado(Decimal("873.45"), 90, 0)
ok("cotizar con decimales: subtotal 1310.175 -> 1310.18", cot["subtotal"] == str(e["subtotal"]) == "1310.18", cot)
ok("cotizar con decimales: comision 131.018 -> 131.02", cot["comision"] == str(e["comision"]) == "131.02", cot)
ok("cotizar con decimales: impuesto 317.064 -> 317.06", cot["impuesto"] == str(e["impuesto"]) == "317.06", cot)
ok("cotizar con decimales: total 1758.26", cot["total"] == str(e["total"]) == "1758.26", cot)
ok("cotizar: las partes suman el total",
   Decimal(cot["subtotal"]) + Decimal(cot["costo_traslado"]) + Decimal(cot["comision"]) + Decimal(cot["impuesto"]) == Decimal(cot["total"]), cot)


seccion("Crear")
MATE = sql("SELECT id FROM materia WHERE nombre = 'Matematica'")
BACHI = sql("SELECT id FROM etapa_educativa WHERE nombre = 'Bachillerato'")
reserva = {"profesor_id": ID["profe4"], "materia_id": MATE, "etapa_id": BACHI, "tema": "  Integrales  ",
           "inicio": futuro(15, 16), "duracion_min": 90, "modalidad": "presencial", "tarjeta_id": TARJETA_A1}
antes = cantidad_clases()
estado, creada = pedir("POST", "/clases", reserva, token=alumno1)
ok("crear 201", estado == 201, creada)
ok("crear: forma de ClaseCreadaOut", set(creada) == {"id", "estado", "total", "cobro"} and creada["estado"] == "pendiente", creada)
ok("crear: cobro retenido", creada["cobro"] == {"estado": "retenido"}, creada)
ok("crear: total IDENTICO al de cotizar", creada["total"] == cot["total"] == "1758.26", (creada["total"], cot["total"]))
CLASE_DECIMALES = creada["id"]
ok("crear: importes congelados en la clase",
   sql("SELECT precio_hora::text || '|' || subtotal || '|' || impuesto || '|' || total FROM clase WHERE id = :i", i=CLASE_DECIMALES)
   == "873.45|1310.18|317.06|1758.26")
ok("crear: fin = inicio + duracion", sql("SELECT extract(epoch FROM fin - inicio)::int FROM clase WHERE id = :i", i=CLASE_DECIMALES) == 5400)
ok("crear: tema sin espacios", sql("SELECT tema FROM clase WHERE id = :i", i=CLASE_DECIMALES) == "Integrales")
ok("crear: cobro en la base", sql("SELECT estado || '|' || importe FROM cobro WHERE clase_id = :i", i=CLASE_DECIMALES) == "retenido|1758.26")
ok("crear: ubicacion = espacio del profesor", sql("SELECT ubicacion FROM clase WHERE id = :i", i=CLASE_DECIMALES) == "Jackson 1045")
ok("crear: una clase mas", cantidad_clases() == antes + 1)

estado, online = pedir("POST", "/clases", {**reserva, "modalidad": "online", "inicio": futuro(16, 16)}, token=alumno1)
ok("crear online: enlace de la videollamada", estado == 201 and sql("SELECT ubicacion FROM clase WHERE id = :i", i=online["id"]) == f"https://meet.exonero.test/clase-{online['id']}", online)
estado, domicilio = pedir("POST", "/clases", {**reserva, "profesor_id": ID["profe2"], "duracion_min": 60, "con_traslado": True,
                                              "inicio": futuro(16, 18), "materia_id": sql("SELECT id FROM materia WHERE nombre = 'Quimica'")}, token=alumno1)
ok("crear a domicilio: total con traslado", estado == 201 and domicilio["total"] == "1342.00", domicilio)
ok("crear a domicilio: ubicacion = casa del alumno",
   sql("SELECT c.ubicacion = p.direccion FROM clase c JOIN perfil_estudiante p ON p.usuario_id = c.estudiante_id WHERE c.id = :i", i=domicilio["id"]))

# Los errores de tarjeta, en un horario que alumno1 todavia no pidio (si no,
# el control de doble pedido responderia 409 antes de mirar la tarjeta).
libre = {**reserva, "inicio": futuro(18, 16)}
antes = cantidad_clases()
error("crear con tarjeta terminada en 0000", pedir("POST", "/clases", {**libre, "tarjeta_id": TARJETA_0000}, token=alumno1), 402, "cobro_rechazado")
ok("cobro rechazado: la clase NO queda creada", cantidad_clases() == antes)
error("crear con tarjeta vencida", pedir("POST", "/clases", {**libre, "tarjeta_id": TARJETA_VENCIDA}, token=alumno1), 402, "tarjeta_vencida")
error("crear con tarjeta de otro alumno", pedir("POST", "/clases", {**libre, "tarjeta_id": TARJETA_A2}, token=alumno1), 404, "tarjeta_no_existe")
error("crear con tarjeta dada de baja", pedir("POST", "/clases", {**libre, "tarjeta_id": otra["id"]}, token=alumno1), 404, "tarjeta_no_existe")
error("crear con tarjeta inexistente", pedir("POST", "/clases", {**libre, "tarjeta_id": 99999}, token=alumno1), 404, "tarjeta_no_existe")
ok("tarjeta mala: ninguna clase de mas", cantidad_clases() == antes)
error("crear como profesor", pedir("POST", "/clases", reserva, token=profe1), 403, "no_es_tuyo")
error("crear materia inexistente", pedir("POST", "/clases", {**reserva, "materia_id": 99999}, token=alumno1), 400, "materia_no_existe")
error("crear etapa inexistente", pedir("POST", "/clases", {**reserva, "etapa_id": 99999}, token=alumno1), 400, "etapa_educativa_no_existe")
error("crear modalidad invalida", pedir("POST", "/clases", {**reserva, "modalidad": "ambas"}, token=alumno1), 400, "modalidad_invalida")
error("crear sin precio", pedir("POST", "/clases", {**reserva, "profesor_id": ID["profe3"]}, token=alumno1), 400, "sin_precio")
error("crear con profesor pausado", pedir("POST", "/clases", {**reserva, "profesor_id": ID["profe8"]}, token=alumno1), 404, "profesor_no_existe")
ok("errores de crear: ninguna clase de mas", cantidad_clases() == antes)


seccion("Historial (lo que hay hasta ahora)")
estado, historial = pedir("GET", "/pagos/historial", token=alumno1)
ok("historial 200", estado == 200 and isinstance(historial, list) and historial, historial)
ok("historial: forma de MovimientoOut",
   set(historial[0]) == {"id", "fecha", "clase_id", "materia", "contraparte", "importe", "estado"}, historial[0])
ok("historial: del mas nuevo al mas viejo", [m["fecha"] for m in historial] == sorted((m["fecha"] for m in historial), reverse=True))
ok("historial: la clase recien creada, retenida, con materia y profesor",
   any(m["clase_id"] == CLASE_DECIMALES and m["estado"] == "retenido" and m["materia"] == "Matematica"
       and m["contraparte"] == "Diego Silva" and m["importe"] == "1758.26" for m in historial), historial[:3])
error("historial como profesor", pedir("GET", "/pagos/historial", token=profe1), 403, "no_es_tuyo")
hoy = fechas.ahora().date()
estado, filtrado = pedir("GET", f"/pagos/historial?desde={hoy}&hasta={hoy}", token=alumno1)
ok("historial filtrado por hoy: trae lo de hoy",
   estado == 200 and any(m["clase_id"] == CLASE_DECIMALES for m in filtrado), filtrado)
ok("historial filtrado por hoy: nada de otros dias",
   all(datetime.fromisoformat(m["fecha"]).astimezone(fechas.ZONA).date() == hoy for m in filtrado), filtrado)
estado, vacio = pedir("GET", "/pagos/historial?desde=2000-01-01&hasta=2000-01-31", token=alumno1)
ok("historial de un rango sin movimientos: lista vacia", estado == 200 and vacio == [], vacio)
estado, _ = pedir("GET", "/pagos/historial?pagina=0", token=alumno1)
ok("historial pagina 0 -> 422", estado == 422, estado)


# ===========================================================================
# BLOQUE B - lo que necesita el panel (1d) y las otras pantallas de lectura
# ===========================================================================

CLASE_OUT = {"id", "estado", "inicio", "duracion_min", "materia", "etapa", "tema", "modalidad",
             "ubicacion", "total", "cobro_estado", "contraparte"}
CONTRAPARTE = {"id", "nombre", "apellido", "foto_base64", "etapa", "centro", "telefono",
               "puntaje_promedio", "cantidad_resenas"}


def momento(iso: str) -> datetime:
    return datetime.fromisoformat(iso).astimezone(fechas.ZONA)


def insertar_clase(estudiante, profesor, inicio: datetime, minutos: int, estado: str) -> int:
    """Una clase cargada a mano (para el periodo anterior de las metricas)."""
    return sql(
        "INSERT INTO clase (estudiante_id, profesor_id, inicio, duracion_min, fin, modalidad, estado, "
        "precio_hora, costo_traslado, pct_comision, pct_iva, subtotal, impuesto, total) "
        "VALUES (:e, :p, :i, :m, :f, 'presencial', :s, 750, 0, 10, 22, 750, 181.50, 1006.50) RETURNING id",
        e=estudiante, p=profesor, i=inicio, m=minutos, f=inicio + timedelta(minutes=minutos), s=estado)


seccion("GET /clases")
estado, clases_a1 = pedir("GET", "/clases", token=alumno1)
ok("GET /clases alumno 200", estado == 200 and isinstance(clases_a1, list) and clases_a1, clases_a1)
ok("GET /clases: forma de ClaseOut (con etapa)", all(set(c) == CLASE_OUT for c in clases_a1), clases_a1[0])
ok("GET /clases: contraparte completa", all(set(c["contraparte"]) == CONTRAPARTE for c in clases_a1))
ok("GET /clases: ordenadas por inicio",
   [momento(c["inicio"]) for c in clases_a1] == sorted(momento(c["inicio"]) for c in clases_a1))
mias = sql("SELECT array_agg(id ORDER BY id) FROM clase WHERE estudiante_id = :u", u=ID["alumno1"])
ok("GET /clases alumno: todas y solo las suyas", sorted(c["id"] for c in clases_a1) == mias, (sorted(c["id"] for c in clases_a1), mias))
ok("GET /clases alumno: la contraparte es el profesor, con puntaje",
   all(c["contraparte"]["id"] == sql("SELECT profesor_id FROM clase WHERE id = :i", i=c["id"])
       and c["contraparte"]["puntaje_promedio"] is not None and c["contraparte"]["telefono"] is None for c in clases_a1))
fila = next(c for c in clases_a1 if c["id"] == CLASE_DECIMALES)
ok("GET /clases: la clase de 1g con materia, etapa, total y cobro",
   fila["materia"] == "Matematica" and fila["etapa"] == "Bachillerato" and fila["total"] == "1758.26"
   and fila["cobro_estado"] == "retenido" and fila["contraparte"]["nombre"] == "Diego", fila)

estado, clases_p1 = pedir("GET", "/clases", token=profe1)
mias = sql("SELECT array_agg(id ORDER BY id) FROM clase WHERE profesor_id = :u", u=ID["profe1"])
ok("GET /clases profesor: todas y solo las suyas", estado == 200 and sorted(c["id"] for c in clases_p1) == mias)
ok("GET /clases profesor: la contraparte es el alumno, con etapa, centro y telefono",
   all(c["contraparte"]["telefono"] and c["contraparte"]["etapa"] for c in clases_p1), clases_p1[0]["contraparte"])

estado, dictadas = pedir("GET", "/clases?estado=dictada", token=profe1)
ok("GET /clases?estado=dictada: solo dictadas", estado == 200 and dictadas and all(c["estado"] == "dictada" for c in dictadas), dictadas)
error("GET /clases?estado=otra cosa", pedir("GET", "/clases?estado=rechazada", token=profe1), 400, "estado_no_permitido")
error("GET /clases sin token", pedir("GET", "/clases"), 401, "sin_token")
ok("GET /clases?pagina=2: vacia (son menos de 50)", pedir("GET", "/clases?pagina=2", token=profe1) == (200, []))
ok("GET /clases?pagina=1001: 422 (tope de paginas)", pedir("GET", "/clases?pagina=1001", token=profe1)[0] == 422)
ok("GET /clases?hasta=9999-12-31: sin tope, no explota", pedir("GET", "/clases?hasta=9999-12-31", token=profe1)[0] == 200)

# Los bordes del dia, en Montevideo: una clase a las 23:30 de aca ya es el dia
# siguiente en UTC. Con ?desde=D&hasta=D tiene que aparecer el dia D. Se carga
# a mano: a esa hora ningun profesor tiene franja, y con la agenda de P3 la
# API la rechazaria.
noche = insertar_clase(ID["alumno1"], ID["profe4"], datetime.fromisoformat(futuro(17, 23, 30)), 60, "pendiente")
dia_noche = momento(futuro(17, 23, 30)).date()
ids_dia = [c["id"] for c in pedir("GET", f"/clases?desde={dia_noche}&hasta={dia_noche}", token=alumno1)[1]]
ok("rango de un dia: incluye la clase de las 23:30 (hasta inclusive, en Montevideo)", noche in ids_dia, ids_dia)
siguiente = dia_noche + timedelta(days=1)
ids_sig = [c["id"] for c in pedir("GET", f"/clases?desde={siguiente}&hasta={siguiente}", token=alumno1)[1]]
ok("rango del dia siguiente: no la incluye (no se corta en UTC)", noche not in ids_sig, ids_sig)
ok("rango de un dia: solo clases de ese dia",
   all(momento(c["inicio"]).date() == dia_noche for c in pedir("GET", f"/clases?desde={dia_noche}&hasta={dia_noche}", token=alumno1)[1]))


seccion("GET /clases/proxima")
estado, prox = pedir("GET", "/clases/proxima", token=profe1)
siguiente_id = sql("SELECT id FROM clase WHERE profesor_id = :p AND estado = 'aprobada' AND inicio > now() ORDER BY inicio LIMIT 1", p=ID["profe1"])
ok("proxima del profesor 200", estado == 200 and prox["id"] == siguiente_id and prox["estado"] == "aprobada", prox)
ok("proxima: ProximaClaseOut (ClaseOut + minutos_restantes)", set(prox) == CLASE_OUT | {"minutos_restantes"}, prox)
falta = (momento(prox["inicio"]) - fechas.ahora()).total_seconds() / 60
ok("proxima: minutos_restantes cuadra", prox["minutos_restantes"] > 0 and abs(prox["minutos_restantes"] - falta) <= 2, (prox["minutos_restantes"], falta))
ok("proxima del profesor: el alumno con etapa, centro y telefono",
   prox["contraparte"]["etapa"] and prox["contraparte"]["centro"] and prox["contraparte"]["telefono"], prox["contraparte"])
alumno_prox = sql("SELECT correo FROM usuario WHERE id = :i", i=sql("SELECT estudiante_id FROM clase WHERE id = :i", i=siguiente_id))
estado, prox_a = pedir("GET", "/clases/proxima", token=login(alumno_prox))
ok("proxima del alumno: la misma clase, del otro lado", estado == 200 and prox_a["id"] == siguiente_id
   and prox_a["contraparte"]["id"] == ID["profe1"] and prox_a["contraparte"]["cantidad_resenas"] is not None, prox_a)
estado, cuerpo = pedir("GET", "/clases/proxima", token=login("profe7@example.com"))
ok("proxima sin clases aprobadas: 204 sin cuerpo", estado == 204 and cuerpo is None, (estado, cuerpo))


seccion("GET /clases/pendientes")
estado, pend = pedir("GET", "/clases/pendientes", token=profe4)
esperadas = sql("SELECT array_agg(id ORDER BY inicio, id) FROM clase WHERE profesor_id = :p AND estado = 'pendiente'", p=ID["profe4"])
ok("pendientes del profesor: todas, por inicio", estado == 200 and [p["id"] for p in pend] == esperadas, (pend, esperadas))
ok("pendientes: forma de SolicitudOut",
   set(pend[0]) == {"id", "inicio", "duracion_min", "materia", "tema", "total", "solicitada_el", "alumno"}, pend[0])
ok("pendientes: con el importe congelado y el alumno",
   any(p["id"] == CLASE_DECIMALES and p["total"] == "1758.26" and p["alumno"]["nombre"] == "Mateo"
       and p["alumno"]["telefono"] for p in pend), pend)
error("pendientes como alumno", pedir("GET", "/clases/pendientes", token=alumno1), 403, "no_es_tuyo")


seccion("GET /clases/metricas")
# profe5 tiene en los seeds dos dictadas y una cancelada este mes. Para que
# haya variacion, se le cargan clases en el mes anterior: dos dictadas del
# mismo alumno (60 y 90 min) y una cancelada.
profe5 = login("profe5@example.com")
ID["profe5"] = sql("SELECT id FROM usuario WHERE correo = 'profe5@example.com'")
mes_ant, _ = fechas.rango_periodo("mes", atras=1)
for dias, minutos, estado_clase in ((2, 60, "dictada"), (9, 90, "dictada"), (12, 60, "cancelada")):
    insertar_clase(ID["alumno3"], ID["profe5"], mes_ant + timedelta(days=dias, hours=16), minutos, estado_clase)


def indicadores_sql(profesor, desde, hasta) -> dict:
    """Los indicadores calculados en SQL, por separado, para comparar."""
    p = {"p": profesor, "d": desde, "h": hasta}
    rango = "profesor_id = :p AND inicio >= :d AND inicio < :h"
    dictadas = sql(f"SELECT count(*) FROM clase WHERE {rango} AND estado = 'dictada'", **p)
    canceladas = sql(f"SELECT count(*) FROM clase WHERE {rango} AND estado = 'cancelada'", **p)
    return {
        "alumnos_atendidos": sql(f"SELECT count(DISTINCT estudiante_id) FROM clase WHERE {rango} AND estado = 'dictada'", **p),
        "horas_dictadas": Decimal(sql(f"SELECT coalesce(sum(duracion_min), 0) FROM clase WHERE {rango} AND estado = 'dictada'", **p)) / 60,
        "alumnos_recurrentes": sql(f"SELECT count(*) FROM (SELECT 1 FROM clase WHERE {rango} AND estado = 'dictada' "
                                   "GROUP BY estudiante_id HAVING count(*) >= 2) x", **p),
        "tasa_cancelacion": Decimal(canceladas) * 100 / (canceladas + dictadas) if canceladas + dictadas else Decimal(0),
    }


REDONDEO = {"alumnos_atendidos": Decimal("1"), "horas_dictadas": Decimal("0.01"),
            "alumnos_recurrentes": Decimal("1"), "tasa_cancelacion": Decimal("0.1")}


def var_esperada(actual, anterior: Decimal, clave: str):
    """La variacion que deberia dar: sobre los valores ya redondeados, con un decimal."""
    anterior = Decimal(anterior).quantize(REDONDEO[clave], ROUND_HALF_UP)
    if not anterior:
        return None
    return float(((Decimal(actual) - anterior) * 100 / anterior).quantize(Decimal("0.1"), ROUND_HALF_UP))


for periodo in ("mes", "trimestre", "anio"):
    estado, m = pedir("GET", f"/clases/metricas?periodo={periodo}", token=profe5)
    ok(f"metricas {periodo} 200", estado == 200 and set(m) == {"alumnos_atendidos", "horas_dictadas", "alumnos_recurrentes",
                                                                "tasa_cancelacion", "variacion"}, m)
    actual = indicadores_sql(ID["profe5"], *fechas.rango_periodo(periodo))
    anterior = indicadores_sql(ID["profe5"], *fechas.rango_periodo(periodo, atras=1))
    ok(f"metricas {periodo}: los cuatro numeros cuadran con SQL",
       m["alumnos_atendidos"] == actual["alumnos_atendidos"]
       and Decimal(m["horas_dictadas"]) == actual["horas_dictadas"].quantize(Decimal("0.01"), ROUND_HALF_UP)
       and m["alumnos_recurrentes"] == actual["alumnos_recurrentes"]
       and Decimal(m["tasa_cancelacion"]) == actual["tasa_cancelacion"].quantize(Decimal("0.1"), ROUND_HALF_UP), (m, actual))
    ok(f"metricas {periodo}: variacion de los cuatro (o null si el anterior es 0)",
       set(m["variacion"]) == set(REDONDEO)
       and all(m["variacion"][k] == var_esperada(m[k], anterior[k], k) for k in REDONDEO), (m["variacion"], anterior))
estado, m = pedir("GET", "/clases/metricas?periodo=mes", token=profe5)
ok("metricas mes: el mes anterior tenia 1 alumno, 2,5 h, 1 recurrente, 33,3 % de cancelacion -> variaciones numericas",
   all(isinstance(m["variacion"][k], float) for k in m["variacion"]), m["variacion"])
ant = indicadores_sql(ID["profe5"], *fechas.rango_periodo("mes", atras=1))
ok("metricas mes: el anterior es el que se cargo a mano",
   ant["alumnos_atendidos"] == 1 and ant["horas_dictadas"] == Decimal("2.5") and ant["alumnos_recurrentes"] == 1, ant)
ok("metricas mes: variacion de horas = (actual - 2,5) / 2,5",
   m["variacion"]["horas_dictadas"] == round(float((Decimal(m["horas_dictadas"]) - Decimal("2.5")) * 100 / Decimal("2.5")), 1), m)
ok("metricas mes: tasa_cancelacion en porcentaje (0 a 100)", Decimal("0") <= Decimal(m["tasa_cancelacion"]) <= 100, m)
ok("metricas: variacion null cuando el anterior es 0",
   pedir("GET", "/clases/metricas?periodo=mes", token=profe1)[1]["variacion"]["alumnos_atendidos"] is None)
error("metricas periodo invalido", pedir("GET", "/clases/metricas?periodo=semana", token=profe5), 400, "periodo_invalido")
error("metricas como alumno", pedir("GET", "/clases/metricas", token=alumno1), 403, "no_es_tuyo")


seccion("GET /clases/series")
INICIO_TRAMO = {"semana": lambda d: d.weekday() == 0, "mes": lambda d: d.day == 1, "anio": lambda d: d.month == 1 and d.day == 1}
TRAMOS = {"semana": 10, "mes": 12, "anio": 5}
for agrupar in ("semana", "mes", "anio"):
    estado, serie = pedir("GET", f"/clases/series?agrupar={agrupar}", token=profe1)
    desde, hasta, _ = fechas.ventana(agrupar)
    total = sql("SELECT count(*) FROM clase WHERE profesor_id = :p AND inicio >= :d AND inicio < :h", p=ID["profe1"], d=desde, h=hasta)
    ok(f"series {agrupar} 200 y forma", estado == 200 and serie and all(set(p) == {"etiqueta", "cantidad", "estado"} for p in serie), serie)
    ok(f"series {agrupar}: ordenada por etiqueta", [p["etiqueta"] for p in serie] == sorted(p["etiqueta"] for p in serie))
    ok(f"series {agrupar}: etiquetas al inicio del tramo", all(INICIO_TRAMO[agrupar](date.fromisoformat(p["etiqueta"])) for p in serie), serie)
    ok(f"series {agrupar}: a lo sumo {TRAMOS[agrupar]} tramos", len({p["etiqueta"] for p in serie}) <= TRAMOS[agrupar])
    ok(f"series {agrupar}: suma igual a las clases de la ventana", sum(p["cantidad"] for p in serie) == total, (serie, total))
error("series agrupacion invalida", pedir("GET", "/clases/series?agrupar=dia", token=profe1), 400, "agrupacion_invalida")
error("series como alumno", pedir("GET", "/clases/series", token=alumno1), 403, "no_es_tuyo")


seccion("GET /pagos/ingresos")
for periodo in ("mes", "trimestre", "anio"):
    desde, hasta = fechas.rango_periodo(periodo)
    cobrado = sql("SELECT coalesce(sum(co.importe), 0) FROM cobro co JOIN clase c ON c.id = co.clase_id "
                  "WHERE c.profesor_id = :p AND co.estado = 'cobrado' AND co.cobrado_el >= :d AND co.cobrado_el < :h",
                  p=ID["profe1"], d=desde, h=hasta)
    for agrupar in ("semana", "mes", "anio"):
        estado, ing = pedir("GET", f"/pagos/ingresos?periodo={periodo}&agrupar={agrupar}", token=profe1)
        ok(f"ingresos {periodo}/{agrupar} 200", estado == 200 and set(ing) == {"cobrado", "pendiente", "promedio_por_clase", "serie"}, ing)
        ok(f"ingresos {periodo}/{agrupar}: cobrado cuadra con SQL", Decimal(ing["cobrado"]) == cobrado, (ing["cobrado"], cobrado))
        ok(f"ingresos {periodo}/{agrupar}: serie con etiquetas al inicio del tramo",
           all(INICIO_TRAMO[agrupar](date.fromisoformat(p["etiqueta"])) and set(p) == {"etiqueta", "importe"} for p in ing["serie"]), ing["serie"])
estado, ing = pedir("GET", "/pagos/ingresos?periodo=mes", token=profe1)
dictadas_mes = sql("SELECT count(*) FROM clase WHERE profesor_id = :p AND estado = 'dictada' AND inicio >= :d AND inicio < :h",
                   p=ID["profe1"], d=fechas.rango_periodo("mes")[0], h=fechas.rango_periodo("mes")[1])
ok("ingresos: promedio = cobrado / dictadas del periodo",
   Decimal(ing["promedio_por_clase"]) == (Decimal(ing["cobrado"]) / dictadas_mes).quantize(Decimal("0.01"), ROUND_HALF_UP), (ing, dictadas_mes))
ok("ingresos: pendiente = lo retenido", Decimal(ing["pendiente"]) == sql(
   "SELECT coalesce(sum(co.importe), 0) FROM cobro co JOIN clase c ON c.id = co.clase_id WHERE c.profesor_id = :p "
   "AND co.estado = 'retenido' AND co.retenido_el >= :d", p=ID["profe1"], d=fechas.rango_periodo("mes")[0]), ing)
ok("ingresos: la serie suma lo cobrado de la ventana", sum(Decimal(p["importe"]) for p in ing["serie"]) == sql(
   "SELECT coalesce(sum(co.importe), 0) FROM cobro co JOIN clase c ON c.id = co.clase_id WHERE c.profesor_id = :p "
   "AND co.estado = 'cobrado' AND co.cobrado_el >= :d", p=ID["profe1"], d=fechas.ventana("semana")[0]), ing["serie"])
ok("ingresos sin dictadas: promedio 0", pedir("GET", "/pagos/ingresos", token=login("profe7@example.com"))[1]["promedio_por_clase"] == "0.00")
error("ingresos periodo invalido", pedir("GET", "/pagos/ingresos?periodo=semana", token=profe1), 400, "periodo_invalido")
error("ingresos agrupacion invalida", pedir("GET", "/pagos/ingresos?agrupar=trimestre", token=profe1), 400, "agrupacion_invalida")
error("ingresos como alumno", pedir("GET", "/pagos/ingresos", token=alumno1), 403, "no_es_tuyo")


seccion("mis-profesores y mis-alumnos")
estado, mp = pedir("GET", "/clases/mis-profesores", token=alumno1)
esperados = sql("SELECT count(DISTINCT profesor_id) FROM clase WHERE estudiante_id = :u AND estado = 'dictada'", u=ID["alumno1"])
ok("mis-profesores 200: uno por profesor con clase dictada", estado == 200 and len(mp) == esperados and esperados > 0, mp)
ok("mis-profesores: forma de PersonaConResena", all(set(p) == {"persona", "cantidad_clases", "ultima_clase", "mi_resena"} for p in mp))
ok("mis-profesores: persona con materias y precio_hora",
   all({"id", "nombre", "apellido", "materias", "precio_hora"} <= set(p["persona"]) for p in mp), mp)
ok("mis-profesores: cantidad_clases = dictadas",
   all(p["cantidad_clases"] == sql("SELECT count(*) FROM clase WHERE estudiante_id = :u AND profesor_id = :p AND estado = 'dictada'",
                                   u=ID["alumno1"], p=p["persona"]["id"]) for p in mp))
ok("mis-profesores: mi_resena null mientras P3 no este", all(p["mi_resena"] is None for p in mp))
error("mis-profesores como profesor", pedir("GET", "/clases/mis-profesores", token=profe1), 403, "no_es_tuyo")
estado, ma = pedir("GET", "/clases/mis-alumnos", token=profe1)
esperados = sql("SELECT count(DISTINCT estudiante_id) FROM clase WHERE profesor_id = :u AND estado = 'dictada'", u=ID["profe1"])
ok("mis-alumnos 200", estado == 200 and len(ma) == esperados and esperados > 0, ma)
ok("mis-alumnos: sin materias ni precio", all("materias" not in p["persona"] and "precio_hora" not in p["persona"] for p in ma), ma)
ok("mis-alumnos: la mas reciente primero", [p["ultima_clase"] for p in ma] == sorted((p["ultima_clase"] for p in ma), key=momento, reverse=True))
error("mis-alumnos como alumno", pedir("GET", "/clases/mis-alumnos", token=alumno1), 403, "no_es_tuyo")


seccion("Lo que consumen agenda y resenas")
from app.modulos.clases import logica as clases_logica  # noqa: E402

with SesionLocal() as db:
    todas = clases_logica.clases_entre(db, ID["profe1"], None, None)
    ok("clases_entre sin pagina: todas las del profesor",
       sorted(c["id"] for c in todas) == sql("SELECT array_agg(id ORDER BY id) FROM clase WHERE profesor_id = :p", p=ID["profe1"]))
    aprobada = sql("SELECT id FROM clase WHERE profesor_id = :p AND estado = 'aprobada' LIMIT 1", p=ID["profe1"])
    ini = sql("SELECT inicio FROM clase WHERE id = :i", i=aprobada)
    cruce = clases_logica.clases_aprobadas_entre(db, ID["profe1"], ini + timedelta(minutes=30), ini + timedelta(hours=5))
    ok("clases_aprobadas_entre: una que empieza antes del rango y lo pisa", [c["id"] for c in cruce] == [aprobada], cruce)
    ok("clases_aprobadas_entre: forma", set(cruce[0]) == {"id", "inicio", "fin", "duracion_min", "estudiante_id"}, cruce)
    pend_id = sql("SELECT id FROM clase WHERE profesor_id = :p AND estado = 'pendiente' LIMIT 1", p=ID["profe1"])
    pini = sql("SELECT inicio FROM clase WHERE id = :i", i=pend_id)
    ok("clases_aprobadas_entre: las pendientes no ocupan",
       clases_logica.clases_aprobadas_entre(db, ID["profe1"], pini, pini + timedelta(hours=1)) == [])
    ok("clases_aprobadas_entre: rango que termina justo cuando empieza: no la incluye",
       clases_logica.clases_aprobadas_entre(db, ID["profe1"], ini - timedelta(hours=1), ini) == [])
    par = db.execute(text("SELECT estudiante_id, profesor_id FROM clase WHERE estado = 'dictada' LIMIT 1")).one()
    ok("tuvieron_clase: alumno y profe con una dictada", clases_logica.tuvieron_clase(db, par.estudiante_id, par.profesor_id) is True)
    ok("tuvieron_clase: en cualquier sentido", clases_logica.tuvieron_clase(db, par.profesor_id, par.estudiante_id) is True)
    ok("tuvieron_clase: alumno1 y profe4 (solo pendientes) -> False", clases_logica.tuvieron_clase(db, ID["alumno1"], ID["profe4"]) is False)


# ===========================================================================
# BLOQUE C - aprobar, rechazar, cancelar, reprogramar, completar
# ===========================================================================

def cobro(clase_id: int) -> str | None:
    return sql("SELECT estado::text FROM cobro WHERE clase_id = :i", i=clase_id)


def esperar_cobro(clase_id: int, estado_buscado: str, segundos: float = 5) -> bool:
    """El reembolso corre en segundo plano: se espera un poco a que llegue."""
    limite = time.monotonic() + segundos
    while time.monotonic() < limite:
        if cobro(clase_id) == estado_buscado:
            return True
        time.sleep(0.2)
    return False


def reservar(token: str, profesor: str, dias: int, hora: int, minuto: int = 0, **cambios) -> int:
    estado, cuerpo = pedir("POST", "/clases", {**reserva, "profesor_id": ID[profesor], "duracion_min": 60,
                                               "inicio": futuro(dias, hora, minuto), "tarjeta_id": cambios.pop("tarjeta", TARJETA_A1),
                                               **cambios}, token=token)
    assert estado == 201, (estado, cuerpo)
    return cuerpo["id"]


seccion("Flujo completo: cotizar -> crear -> aprobar -> cancelar (reembolso en segundo plano)")
cot = pedir("POST", "/clases/cotizar", {"profesor_id": ID["profe1"], "duracion_min": 60, "modalidad": "presencial"})[1]
estado, creada = pedir("POST", "/clases", {**reserva, "profesor_id": ID["profe1"], "duracion_min": 60,
                                           "inicio": futuro(20, 15)}, token=alumno1)
ok("flujo: crear 201 retenido, con el total de cotizar", estado == 201 and creada["cobro"]["estado"] == "retenido"
   and creada["total"] == cot["total"], creada)
CLASE = creada["id"]
estado, aprobada = pedir("POST", f"/clases/{CLASE}/aprobar", token=profe1)
ok("flujo: aprobar 200 -> aprobada y cobrado", estado == 200 and aprobada == {"id": CLASE, "estado": "aprobada",
                                                                               "total": cot["total"], "cobro": {"estado": "cobrado"}}, aprobada)
ok("flujo: cobrado_el registrado", sql("SELECT cobrado_el IS NOT NULL FROM cobro WHERE clase_id = :i", i=CLASE))
ok("flujo: aparece como proxima del alumno o mas adelante",
   any(c["id"] == CLASE and c["estado"] == "aprobada" and c["cobro_estado"] == "cobrado" for c in pedir("GET", "/clases", token=alumno1)[1]))
estado, cancelada = pedir("POST", f"/clases/{CLASE}/cancelar", {"motivo": "  Me surgio un parcial  "}, token=alumno1)
ok("flujo: cancelar 200, cancelada por el estudiante", estado == 200 and cancelada["estado"] == "cancelada"
   and cancelada["cancelada_por"] == "estudiante", cancelada)
ok("flujo: reembolso en_proceso por el total", cancelada.get("reembolso") == {"estado": "en_proceso", "importe": cot["total"]}, cancelada)
ok("flujo: el cobro termina reembolsado (BackgroundTask)", esperar_cobro(CLASE, "reembolsado"), cobro(CLASE))
ok("flujo: reembolsado_el registrado", sql("SELECT reembolsado_el IS NOT NULL FROM cobro WHERE clase_id = :i", i=CLASE))
ok("flujo: la clase NO se borro y guarda el motivo",
   sql("SELECT estado || '|' || cancelada_por || '|' || motivo FROM clase WHERE id = :i", i=CLASE) == "cancelada|estudiante|Me surgio un parcial")
antes_reembolso = sql("SELECT reembolsado_el FROM cobro WHERE clase_id = :i", i=CLASE)
from app.modulos.pagos import logica as pagos_logica  # noqa: E402
pagos_logica.reembolsar(CLASE)
ok("reembolsar es idempotente: la segunda vez no toca nada",
   cobro(CLASE) == "reembolsado" and sql("SELECT reembolsado_el FROM cobro WHERE clase_id = :i", i=CLASE) == antes_reembolso)
ok("historial: el reembolso aparece", any(m["clase_id"] == CLASE and m["estado"] == "reembolsado"
                                          for m in pedir("GET", "/pagos/historial", token=alumno1)[1]))
error("cancelar una ya cancelada", pedir("POST", f"/clases/{CLASE}/cancelar", {}, token=alumno1), 409, "estado_invalido")


seccion("Flujo completo: crear -> rechazar")
CLASE = reservar(alumno1, "profe1", 20, 17)
cobro_id = sql("SELECT id FROM cobro WHERE clase_id = :i", i=CLASE)
estado, cuerpo = pedir("DELETE", f"/clases/{CLASE}", token=profe1)
ok("rechazar 204 sin cuerpo", estado == 204 and cuerpo is None, (estado, cuerpo))
ok("rechazar: la clase desaparece", sql("SELECT count(*) FROM clase WHERE id = :i", i=CLASE) == 0)
ok("rechazar: el cobro QUEDA, liberado y sin clase",
   sql("SELECT estado || '|' || (clase_id IS NULL) || '|' || (liberado_el IS NOT NULL) FROM cobro WHERE id = :i", i=cobro_id) == "liberado|true|true")
mov = next((m for m in pedir("GET", "/pagos/historial", token=alumno1)[1] if m["id"] == cobro_id), None)
ok("rechazar: aparece en el historial del alumno, sin clase ni materia ni contraparte",
   mov is not None and mov["estado"] == "liberado" and mov["clase_id"] is None and mov["materia"] is None
   and mov["contraparte"] is None and mov["importe"] == "1207.80", mov)
error("rechazar una que ya no existe", pedir("DELETE", f"/clases/{CLASE}", token=profe1), 404, "clase_no_existe")


seccion("Dos solicitudes sobre el mismo horario")
alumno3 = login("alumno3@example.com")
TARJETA_A3 = pedir("GET", "/pagos/tarjetas", token=alumno3)[1][0]["id"]
primera = reservar(alumno1, "profe1", 21, 16)
segunda = reservar(alumno2, "profe1", 21, 16, tarjeta=TARJETA_A2)
encimada = reservar(alumno3, "profe1", 21, 16, 30, tarjeta=TARJETA_A3)
ok("dos pendientes encimadas son legitimas", sql("SELECT count(*) FROM clase WHERE id IN (:a, :b) AND estado = 'pendiente'", a=primera, b=segunda) == 2)
antes = cantidad_clases()
error("el MISMO alumno pidiendo de nuevo ese rato (doble clic)",
      pedir("POST", "/clases", {**reserva, "profesor_id": ID["profe1"], "duracion_min": 60, "inicio": futuro(21, 16, 30)}, token=alumno1),
      409, "horario_ocupado")
ok("doble clic: no queda una segunda clase ni un segundo cobro retenido", cantidad_clases() == antes)
ayer = (fechas.ahora() - timedelta(days=1)).replace(hour=16, minute=0, second=0, microsecond=0).isoformat()
error("reservar un horario que ya paso", pedir("POST", "/clases", {**reserva, "inicio": ayer}, token=alumno1), 409, "horario_ocupado")
error("reprogramar a un horario que ya paso", pedir("POST", f"/clases/{primera}/reprogramar", {"inicio": ayer}, token=alumno1), 409, "horario_ocupado")
ok("reprogramar fallido: la clase no se movio",
   sql("SELECT inicio = :i FROM clase WHERE id = :c", i=datetime.fromisoformat(futuro(21, 16)), c=primera))
ok("aprobar la primera 200", pedir("POST", f"/clases/{primera}/aprobar", token=profe1)[0] == 200)
error("aprobar la segunda: la EXCLUDE la frena", pedir("POST", f"/clases/{segunda}/aprobar", token=profe1), 409, "horario_ocupado")
error("aprobar una que se cruza media hora", pedir("POST", f"/clases/{encimada}/aprobar", token=profe1), 409, "horario_ocupado")
ok("la segunda sigue pendiente, con el cobro retenido", sql("SELECT estado::text FROM clase WHERE id = :i", i=segunda) == "pendiente"
   and cobro(segunda) == "retenido")
estado, cancel_pend = pedir("POST", f"/clases/{segunda}/cancelar", {"motivo": None}, token=profe1)
ok("cancelar una pendiente (el profesor): se libera en el momento",
   estado == 200 and cancel_pend["cancelada_por"] == "profesor" and cancel_pend["reembolso"]["estado"] == "liberado"
   and cobro(segunda) == "liberado", cancel_pend)
ok("cancelada la primera, la encimada se puede aprobar",
   pedir("POST", f"/clases/{primera}/cancelar", {}, token=profe1)[0] == 200
   and pedir("POST", f"/clases/{encimada}/aprobar", token=profe1)[0] == 200)


seccion("Roles cruzados, ids inexistentes y estados invalidos")
CLASE = reservar(alumno1, "profe1", 22, 15)
error("aprobar como alumno", pedir("POST", f"/clases/{CLASE}/aprobar", token=alumno1), 403, "no_es_tuyo")
error("aprobar la clase de otro profesor", pedir("POST", f"/clases/{CLASE}/aprobar", token=profe2), 403, "no_es_tuyo")
error("rechazar la clase de otro profesor", pedir("DELETE", f"/clases/{CLASE}", token=profe2), 403, "no_es_tuyo")
error("rechazar como alumno", pedir("DELETE", f"/clases/{CLASE}", token=alumno1), 403, "no_es_tuyo")
error("cancelar la clase de otro alumno", pedir("POST", f"/clases/{CLASE}/cancelar", {}, token=alumno2), 403, "no_es_tuyo")
error("cancelar la clase de otro profesor", pedir("POST", f"/clases/{CLASE}/cancelar", {}, token=profe2), 403, "no_es_tuyo")
error("reprogramar la clase de otro", pedir("POST", f"/clases/{CLASE}/reprogramar", {"inicio": futuro(23, 15)}, token=alumno2), 403, "no_es_tuyo")
error("completar como alumno", pedir("POST", f"/clases/{CLASE}/completar", {"estado": "dictada"}, token=alumno1), 403, "no_es_tuyo")
error("completar la de otro profesor", pedir("POST", f"/clases/{CLASE}/completar", {"estado": "dictada"}, token=profe2), 403, "no_es_tuyo")
for metodo, ruta, cuerpo in (("POST", "/clases/99999/aprobar", None), ("DELETE", "/clases/99999", None),
                             ("POST", "/clases/99999/cancelar", {}), ("POST", "/clases/99999/reprogramar", {"inicio": futuro(23, 15)}),
                             ("POST", "/clases/99999/completar", {"estado": "dictada"})):
    error(f"{metodo} {ruta} inexistente", pedir(metodo, ruta, cuerpo, token=profe1 if "reprogramar" not in ruta and "cancelar" not in ruta else alumno1), 404, "clase_no_existe")
error("completar una pendiente", pedir("POST", f"/clases/{CLASE}/completar", {"estado": "dictada"}, token=profe1), 409, "estado_invalido")
pedir("POST", f"/clases/{CLASE}/aprobar", token=profe1)
error("aprobar una ya aprobada", pedir("POST", f"/clases/{CLASE}/aprobar", token=profe1), 409, "estado_invalido")
error("rechazar una aprobada", pedir("DELETE", f"/clases/{CLASE}", token=profe1), 409, "estado_invalido")
error("completar con un estado que no es dictada ni no_asistida",
      pedir("POST", f"/clases/{CLASE}/completar", {"estado": "cancelada"}, token=profe1), 400, "estado_no_permitido")
DICTADA = sql("SELECT id FROM clase WHERE profesor_id = :p AND estado = 'dictada' LIMIT 1", p=ID["profe1"])
alumno_dictada = login(sql("SELECT u.correo FROM usuario u JOIN clase c ON c.estudiante_id = u.id WHERE c.id = :i", i=DICTADA))
error("cancelar una dictada", pedir("POST", f"/clases/{DICTADA}/cancelar", {}, token=alumno_dictada), 409, "estado_invalido")
error("reprogramar una dictada", pedir("POST", f"/clases/{DICTADA}/reprogramar", {"inicio": futuro(23, 15)}, token=alumno_dictada), 409, "estado_invalido")
error("completar una dictada", pedir("POST", f"/clases/{DICTADA}/completar", {"estado": "dictada"}, token=profe1), 409, "estado_invalido")
error("aprobar sin token", pedir("POST", f"/clases/{CLASE}/aprobar"), 401, "sin_token")


seccion("Reprogramar una aprobada y volver a aprobarla")
estado, prog = pedir("POST", f"/clases/{CLASE}/reprogramar", {"inicio": futuro(22, 18), "duracion_min": 60}, token=alumno1)
ok("reprogramar 200 -> pendiente, con el horario nuevo", estado == 200 and prog["estado"] == "pendiente"
   and momento(prog["inicio"]) == momento(futuro(22, 18)), prog)
ok("reprogramar: devuelve ClaseOut", set(prog) == CLASE_OUT, prog)
ok("reprogramar: el importe no cambia y el cobro sigue cobrado", prog["total"] == "1207.80" and prog["cobro_estado"] == "cobrado", prog)
ok("reprogramar: fin = inicio nuevo + duracion",
   sql("SELECT extract(epoch FROM fin - inicio)::int FROM clase WHERE id = :i", i=CLASE) == 3600)
cobrado_el = sql("SELECT cobrado_el FROM cobro WHERE clase_id = :i", i=CLASE)
estado, re_aprobada = pedir("POST", f"/clases/{CLASE}/aprobar", token=profe1)
ok("volver a aprobarla 200, cobro cobrado", estado == 200 and re_aprobada["estado"] == "aprobada"
   and re_aprobada["cobro"]["estado"] == "cobrado", re_aprobada)
ok("volver a aprobarla: cobrar() no cobra dos veces (cobrado_el igual)",
   sql("SELECT cobrado_el FROM cobro WHERE clase_id = :i", i=CLASE) == cobrado_el)
error("reprogramar cambiando la duracion",
      pedir("POST", f"/clases/{CLASE}/reprogramar", {"inicio": futuro(22, 18), "duracion_min": 90}, token=alumno1), 400, "duracion_no_modificable")
estado, prog = pedir("POST", f"/clases/{CLASE}/reprogramar", {"inicio": futuro(22, 18, 30)}, token=profe1)
ok("reprogramar la puede pedir el profesor, y media hora sobre si misma no choca", estado == 200 and prog["estado"] == "pendiente", prog)
# El caso borde: el profesor rechaza la reprogramacion de una clase ya cobrada.
cobro_id = sql("SELECT id FROM cobro WHERE clase_id = :i", i=CLASE)
ok("rechazar una reprogramada que ya estaba cobrada: 204", pedir("DELETE", f"/clases/{CLASE}", token=profe1)[0] == 204)
ok("...y la plata se devuelve: el cobro queda reembolsado, sin clase",
   sql("SELECT estado || '|' || (clase_id IS NULL) FROM cobro WHERE id = :i", i=cobro_id) == "reembolsado|true")


seccion("Completar")
dictadas_antes = sql("SELECT clases_dictadas FROM perfil_profesor WHERE usuario_id = :p", p=ID["profe4"])
with SesionLocal() as db:
    ok("antes: alumno1 y profe4 no tuvieron clase", clases_logica.tuvieron_clase(db, ID["alumno1"], ID["profe4"]) is False)
pedir("POST", f"/clases/{CLASE_DECIMALES}/aprobar", token=profe4)
estado, hecha = pedir("POST", f"/clases/{CLASE_DECIMALES}/completar", {"estado": "dictada"}, token=profe4)
ok("completar 200 -> dictada", estado == 200 and hecha["estado"] == "dictada" and set(hecha) == CLASE_OUT, hecha)
ok("completar: clases_dictadas sube uno",
   sql("SELECT clases_dictadas FROM perfil_profesor WHERE usuario_id = :p", p=ID["profe4"]) == dictadas_antes + 1)
with SesionLocal() as db:
    ok("completar: tuvieron_clase da True", clases_logica.tuvieron_clase(db, ID["alumno1"], ID["profe4"]) is True)
    ok("completar: tuvieron_clase en el otro sentido", clases_logica.tuvieron_clase(db, ID["profe4"], ID["alumno1"]) is True)
ok("completar: profe4 aparece en mis-profesores de alumno1",
   any(p["persona"]["id"] == ID["profe4"] and p["cantidad_clases"] == 1 for p in pedir("GET", "/clases/mis-profesores", token=alumno1)[1]))
ok("completar: la ficha publica muestra la clase dictada",
   pedir("GET", f"/profesores/{ID['profe4']}")[1]["clases_dictadas"] == dictadas_antes + 1)
pedir("POST", f"/clases/{online['id']}/aprobar", token=profe4)
estado, falto = pedir("POST", f"/clases/{online['id']}/completar", {"estado": "no_asistida"}, token=profe4)
ok("completar no_asistida: 200 y NO suma dictadas", estado == 200 and falto["estado"] == "no_asistida"
   and sql("SELECT clases_dictadas FROM perfil_profesor WHERE usuario_id = :p", p=ID["profe4"]) == dictadas_antes + 1, falto)
ok("no_asistida: el cobro queda cobrado", cobro(online["id"]) == "cobrado")


# ===========================================================================
# SISTEMA - la app importa, la migracion va y vuelve, los seeds cuadran
# ===========================================================================

def correr(*argumentos: str) -> subprocess.CompletedProcess:
    """python <argumentos>, con el mismo interprete y desde backend/."""
    return subprocess.run([sys.executable, *argumentos], capture_output=True, text=True)


seccion("La app, la migracion y los seeds")
r = correr("-c", "from app.main import app; print(len(app.routes))")
ok("python -c 'from app.main import app'", r.returncode == 0, r.stderr[-400:])
r = correr("-m", "alembic", "check")
ok("alembic check: sin diferencias", r.returncode == 0 and "No new upgrade operations" in r.stdout + r.stderr, r.stderr[-400:])
r = correr("-m", "alembic", "downgrade", "-1")
ok("alembic downgrade -1 (con cobros de clases rechazadas en la base)", r.returncode == 0, r.stderr[-400:])
ok("downgrade: clase_id vuelve a NOT NULL con CASCADE", sql(
   "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'cobro' AND column_name = 'clase_id'") == "NO")
r = correr("-m", "alembic", "upgrade", "head")
ok("alembic upgrade head", r.returncode == 0, r.stderr[-400:])
ok("upgrade: clase_id nullable", sql(
   "SELECT is_nullable FROM information_schema.columns WHERE table_name = 'cobro' AND column_name = 'clase_id'") == "YES")
ok("upgrade: la clave foranea es ON DELETE SET NULL", sql(
   "SELECT confdeltype FROM pg_constraint WHERE conname = 'cobro_clase_id_fkey'") == "n")
r = correr("-m", "alembic", "check")
ok("alembic check despues de ir y volver", r.returncode == 0, r.stderr[-400:])

primera, segunda = correr("-m", "app.seeds"), correr("-m", "app.seeds")
ok("seeds dos veces seguidas", primera.returncode == 0 and segunda.returncode == 0, (primera.stderr + segunda.stderr)[-400:])
ok("seeds: sin duplicar nada (20 usuarios, 30 clases, 30 cobros, 12 tarjetas)",
   sql("SELECT (SELECT count(*) FROM usuario) || '|' || (SELECT count(*) FROM clase) || '|' || "
       "(SELECT count(*) FROM cobro) || '|' || (SELECT count(*) FROM tarjeta)") == "20|30|30|12")
with SesionLocal() as db:
    clases_seeds = db.execute(text(
        "SELECT duracion_min, precio_hora, costo_traslado, pct_comision, pct_iva, subtotal, impuesto, total FROM clase")).all()
cuadran = [
    clases_logica.desglosar(c.precio_hora, c.duracion_min, c.costo_traslado, c.pct_comision, c.pct_iva)
    for c in clases_seeds
]
ok("seeds: las 30 clases cuadran con desglosar() (el mismo calculo que el checkout)",
   all((d["subtotal"], d["impuesto"], d["total"]) == (c.subtotal, c.impuesto, c.total) for d, c in zip(cuadran, clases_seeds)))
ok("seeds: cada cobro es el total de su clase",
   sql("SELECT count(*) FROM cobro co JOIN clase c ON c.id = co.clase_id WHERE co.importe <> c.total") == 0)


# ===========================================================================
# Resultado
# ===========================================================================

print(f"\n{pasaron} de {pasaron + len(fallaron)} comprobaciones pasaron.")
if fallaron:
    print("Fallaron:")
    for f in fallaron:
        print("  -", f)
    sys.exit(1)
