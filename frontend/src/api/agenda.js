/**
 * Llamadas al modulo agenda del backend. El modulo es de P3.
 *
 * Por ahora solo esta lo que necesita el checkout (1g, P4). Cuando P3 haga 1i
 * y la disponibilidad de 1f, suma aca el resto de sus endpoints.
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
 * No reserva nada: solo consulta. Mientras P3 no lo implemente responde 500
 * (error_servidor); el checkout sigue igual, porque POST /clases vuelve a
 * verificar y la base tiene la restriccion EXCLUDE.
 */
export function verificarHorario(datos) {
  return pedir('/api/agenda/verificar', { metodo: 'POST', cuerpo: datos })
}
