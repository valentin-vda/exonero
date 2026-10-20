/**
 * Llamadas al modulo clases del backend (P4).
 *
 * Igual que perfiles.js: una funcion por endpoint. Las pantallas llaman a
 * estas funciones y nunca a pedir() directamente.
 *
 * Lo usan:
 *   1g Checkout          cotizar(), crearClase()
 *   1d Panel del profesor proximaClase(), listarClases(), metricas(), series()
 *   1b, 1i (P3)          listarClases(), cancelar, reprogramar, aprobar, ...
 *   1f (P2)              cotizar(), para el estimado de la ficha
 *
 * Errores propios (el texto esta en mensajes.js):
 *   400 sin_precio, 402 cobro_rechazado, 402 tarjeta_vencida,
 *   404 clase_no_existe, 409 horario_ocupado, 409 estado_invalido
 */

import { pedir } from './cliente.js'

/** Arma "?a=1&b=2" sin los valores vacios (null, undefined o ''). */
function consulta(parametros) {
  const limpios = Object.entries(parametros).filter(([, valor]) => valor !== null && valor !== undefined && valor !== '')
  return limpios.length ? `?${new URLSearchParams(limpios)}` : ''
}

// ---------------------------------------------------------------------------
// Reservar - 1f y 1g
// ---------------------------------------------------------------------------

/**
 * POST /api/clases/cotizar - { profesor_id, duracion_min, modalidad, con_traslado }
 * -> { precio_hora, horas, subtotal, costo_traslado, pct_comision, comision,
 *      pct_iva, impuesto, total }
 *
 * EL UNICO calculo de plata. 1f y 1g muestran lo que devuelve esto, nunca
 * hacen la cuenta en el frontend. Los importes llegan como texto ("1913.18"):
 * Pydantic serializa Decimal asi para no perder centesimos.
 */
export function cotizar(datos) {
  return pedir('/api/clases/cotizar', { metodo: 'POST', cuerpo: datos })
}

/**
 * POST /api/clases - el confirmar de 1g.
 * { profesor_id, materia_id, etapa_id, tema, inicio, duracion_min, modalidad,
 *   con_traslado, tarjeta_id } -> { id, estado, total, cobro: { estado } }
 */
export function crearClase(datos) {
  return pedir('/api/clases', { metodo: 'POST', cuerpo: datos })
}

// ---------------------------------------------------------------------------
// Leer - 1a, 1b, 1d, 1i
// ---------------------------------------------------------------------------

/** GET /api/clases/proxima -> ProximaClaseOut, o null si no hay ninguna (204). */
export function proximaClase() {
  return pedir('/api/clases/proxima')
}

/**
 * GET /api/clases?desde=AAAA-MM-DD&hasta=AAAA-MM-DD&estado=...&pagina=1
 * -> [ClaseOut]. El mismo calendario para el alumno y el profesor: el rol sale
 * del token.
 */
export function listarClases({ desde, hasta, estado, pagina } = {}) {
  return pedir(`/api/clases${consulta({ desde, hasta, estado, pagina })}`)
}

/** GET /api/clases/pendientes -> [SolicitudOut]. Solo profesor (1i). */
export function solicitudesPendientes() {
  return pedir('/api/clases/pendientes')
}

/** GET /api/clases/mis-profesores -> [PersonaConResena]. Solo alumno (1b). */
export function misProfesores() {
  return pedir('/api/clases/mis-profesores')
}

/** GET /api/clases/mis-alumnos -> [PersonaConResena]. Solo profesor (1i). */
export function misAlumnos() {
  return pedir('/api/clases/mis-alumnos')
}

// ---------------------------------------------------------------------------
// Panel del profesor - 1d
// ---------------------------------------------------------------------------

/**
 * GET /api/clases/metricas?periodo=mes|trimestre|anio
 * -> { alumnos_atendidos, horas_dictadas, alumnos_recurrentes,
 *      tasa_cancelacion, variacion: { <indicador>: porcentaje } }
 */
export function metricas(periodo = 'mes') {
  return pedir(`/api/clases/metricas${consulta({ periodo })}`)
}

/** GET /api/clases/series?agrupar=semana|mes|anio -> [{ etiqueta, cantidad, estado }] */
export function series(agrupar = 'semana') {
  return pedir(`/api/clases/series${consulta({ agrupar })}`)
}

// ---------------------------------------------------------------------------
// Acciones sobre una clase - 1b y 1i
// ---------------------------------------------------------------------------

/** POST /api/clases/{id}/aprobar -> { id, estado, total, cobro: { estado } } */
export function aprobarClase(id) {
  return pedir(`/api/clases/${id}/aprobar`, { metodo: 'POST' })
}

/** DELETE /api/clases/{id} - rechazar: borra la clase y libera el cobro. */
export function rechazarClase(id) {
  return pedir(`/api/clases/${id}`, { metodo: 'DELETE' })
}

/** POST /api/clases/{id}/cancelar - { motivo } -> { id, estado, cancelada_por, reembolso } */
export function cancelarClase(id, motivo = null) {
  return pedir(`/api/clases/${id}/cancelar`, { metodo: 'POST', cuerpo: { motivo } })
}

/** POST /api/clases/{id}/reprogramar - { inicio, duracion_min } -> ClaseOut */
export function reprogramarClase(id, datos) {
  return pedir(`/api/clases/${id}/reprogramar`, { metodo: 'POST', cuerpo: datos })
}

/** POST /api/clases/{id}/completar - { estado: 'dictada' | 'no_asistida' } -> ClaseOut */
export function completarClase(id, estado = 'dictada') {
  return pedir(`/api/clases/${id}/completar`, { metodo: 'POST', cuerpo: { estado } })
}
