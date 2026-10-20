/**
 * Llamadas al modulo pagos del backend (P4).
 *
 * Las tarjetas son el mismo recurso desde dos pantallas: el alta desde el
 * checkout (1g) y la administracion desde el perfil (1e, "Medios de pago").
 *
 * Errores propios (el texto esta en mensajes.js):
 *   400 tarjeta_invalida, 402 tarjeta_vencida, 404 tarjeta_no_existe
 */

import { pedir } from './cliente.js'

/** Arma "?a=1&b=2" sin los valores vacios (null, undefined o ''). */
function consulta(parametros) {
  const limpios = Object.entries(parametros).filter(([, valor]) => valor !== null && valor !== undefined && valor !== '')
  return limpios.length ? `?${new URLSearchParams(limpios)}` : ''
}

// ---------------------------------------------------------------------------
// Tarjetas - 1e y 1g. Solo estudiante.
// ---------------------------------------------------------------------------

/** GET /api/pagos/tarjetas -> [{ id, marca, ultimos4, titular, vence: 'MM/AA' }] */
export function listarTarjetas() {
  return pedir('/api/pagos/tarjetas')
}

/**
 * POST /api/pagos/tarjetas - { numero, titular, vence_mes, vence_anio, ccv }
 * -> la tarjeta en su version segura (sin numero completo ni CCV).
 * vence_anio va con cuatro cifras (2028), no "28".
 */
export function agregarTarjeta(datos) {
  return pedir('/api/pagos/tarjetas', { metodo: 'POST', cuerpo: datos })
}

/** DELETE /api/pagos/tarjetas/{id} - baja logica. */
export function borrarTarjeta(id) {
  return pedir(`/api/pagos/tarjetas/${id}`, { metodo: 'DELETE' })
}

// ---------------------------------------------------------------------------
// Historial del alumno - 1e
// ---------------------------------------------------------------------------

/**
 * GET /api/pagos/historial?desde=&hasta=&pagina=
 * -> [{ id, fecha, clase_id, materia, contraparte, importe, estado }]
 * estado: retenido | cobrado | liberado | reembolsado
 */
export function historialPagos({ desde, hasta, pagina } = {}) {
  return pedir(`/api/pagos/historial${consulta({ desde, hasta, pagina })}`)
}

// ---------------------------------------------------------------------------
// Ingresos del profesor - 1d (y 1j)
// ---------------------------------------------------------------------------

/**
 * GET /api/pagos/ingresos?periodo=mes|trimestre|anio&agrupar=semana|mes|anio
 * -> { cobrado, pendiente, promedio_por_clase, serie: [{ etiqueta, importe }] }
 */
export function ingresos(periodo = 'mes', agrupar = 'semana') {
  return pedir(`/api/pagos/ingresos${consulta({ periodo, agrupar })}`)
}
