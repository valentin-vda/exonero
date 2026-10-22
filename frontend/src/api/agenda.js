/**
 * Llamadas al modulo agenda del backend. El modulo es de P3.
 *
 * Lo usan:
 *   1f, 1g (P2, P4)  obtenerDisponibilidad(), verificarHorario()
 *   1i Agenda (P3)   todo: la semana, las franjas, los bloqueos
 *   1j (P1)          listarFranjas(), guardarFranjas() (el mismo editor de 1i)
 *
 * Errores propios (el texto esta en mensajes.js):
 *   400 rango_invalido, franja_invalida, bloqueo_invalido
 *   404 profesor_no_existe, bloqueo_no_existe
 *   409 franjas_superpuestas, hay_clase_aprobada, bloqueo_superpuesto
 */

import { pedir } from './cliente.js'

/** GET /api/agenda/profesores/{id}/disponibilidad - los huecos de una semana. */
export function obtenerDisponibilidad(profesorId, desde, hasta, duracion) {
  const parametros = new URLSearchParams({ desde, hasta, duracion })
  return pedir(`/api/agenda/profesores/${profesorId}/disponibilidad?${parametros}`)
}

/**
 * POST /api/agenda/verificar - { profesor_id, inicio, duracion_min }
 * -> { libre: true } o { libre: false, motivo }
 *
 * motivo: ocupado, bloqueado, fuera_de_franja, aviso_minimo, tope_diario.
 * No reserva nada: solo consulta. POST /clases vuelve a verificar igual, y la
 * base tiene la restriccion EXCLUDE.
 */
export function verificarHorario(datos) {
  return pedir('/api/agenda/verificar', { metodo: 'POST', cuerpo: datos })
}

// ---------------------------------------------------------------------------
// Lo que edita el profesor - 1i y 1j. Todas piden rol profesor (403 si no).
// ---------------------------------------------------------------------------

/**
 * GET /api/agenda/yo/semana?desde=AAAA-MM-DD - siete dias desde `desde`.
 * -> { desde, hasta, aprobadas, pendientes, cerradas, bloqueos }
 * Las clases tienen la forma de GET /api/clases (ver clases.js).
 */
export function semanaProfesor(desde) {
  return pedir(`/api/agenda/yo/semana?${new URLSearchParams({ desde })}`)
}

/** GET /api/agenda/yo/franjas -> [{ id, dia_semana, hora_inicio, hora_fin, modalidad, activa }] */
export function listarFranjas() {
  return pedir('/api/agenda/yo/franjas')
}

/**
 * PUT /api/agenda/yo/franjas - { franjas: [...] }: REEMPLAZA todas las franjas.
 * dia_semana es 0 (domingo) a 6 (sabado), como Date.getDay(). Las horas van
 * como 'HH:MM'. Devuelve las franjas guardadas.
 */
export function guardarFranjas(franjas) {
  return pedir('/api/agenda/yo/franjas', { metodo: 'PUT', cuerpo: { franjas } })
}

/** GET /api/agenda/yo/bloqueos[?desde&hasta] - sin rango, los que todavia no terminaron. */
export function listarBloqueos(desde, hasta) {
  const parametros = new URLSearchParams(Object.entries({ desde, hasta }).filter(([, v]) => v))
  const consulta = parametros.toString()
  return pedir(`/api/agenda/yo/bloqueos${consulta ? `?${consulta}` : ''}`)
}

/** POST /api/agenda/yo/bloqueos - { inicio, fin, motivo } con inicio y fin en ISO con zona. */
export function crearBloqueo(datos) {
  return pedir('/api/agenda/yo/bloqueos', { metodo: 'POST', cuerpo: datos })
}

/** DELETE /api/agenda/yo/bloqueos/{id} -> null (204). */
export function borrarBloqueo(id) {
  return pedir(`/api/agenda/yo/bloqueos/${id}`, { metodo: 'DELETE' })
}
