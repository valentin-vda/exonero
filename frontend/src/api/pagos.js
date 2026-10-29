/**
 * Llamadas al modulo pagos del backend (P4).
 *
 * Las tarjetas son el mismo recurso desde dos pantallas: el alta desde el
 * checkout (1g) y la administracion desde el perfil (1e, "Medios de pago").
 * Las cuentas de cobro son del profesor: la tarjeta "Cobros" de 1j.
 *
 * Errores propios (el texto esta en mensajes.js):
 *   tarjetas  400 tarjeta_invalida, 402 tarjeta_vencida, 404 tarjeta_no_existe
 *   cuentas   400 cuenta_invalida, 400 banco_no_existe, 400 correo_invalido,
 *             404 cuenta_no_existe, 409 cuenta_repetida
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

// ---------------------------------------------------------------------------
// Cuentas de cobro del profesor - 1j. Solo profesor.
// ---------------------------------------------------------------------------

/**
 * GET /api/pagos/cuentas
 * -> [{ id, tipo, banco, banco_nombre, visible, titular, moneda, es_principal }]
 * La principal viene primero. tipo: banco | mercado_pago. visible es
 * "•••• 3391" en un banco (nunca el numero entero) y el correo en Mercado Pago.
 */
export function listarCuentasCobro() {
  return pedir('/api/pagos/cuentas')
}

/**
 * POST /api/pagos/cuentas -> la cuenta, con la misma forma que en la lista.
 *   banco:        { tipo: 'banco', banco: 'brou', identificador: '001234567', moneda: 'UYU', titular }
 *   Mercado Pago: { tipo: 'mercado_pago', identificador: 'correo@example.com' }
 * La primera que se agrega queda como principal.
 */
export function agregarCuentaCobro(datos) {
  return pedir('/api/pagos/cuentas', { metodo: 'POST', cuerpo: datos })
}

/**
 * PUT /api/pagos/cuentas/{id}/principal -> TODAS las cuentas, ya reordenadas
 * (cambian dos: la nueva principal y la que lo era).
 */
export function hacerPrincipal(id) {
  return pedir(`/api/pagos/cuentas/${id}/principal`, { metodo: 'PUT' })
}

/**
 * DELETE /api/pagos/cuentas/{id} - baja logica. Si era la principal, el
 * backend hace principal a la mas vieja que queda: hay que volver a pedir la
 * lista para saber cual.
 */
export function quitarCuentaCobro(id) {
  return pedir(`/api/pagos/cuentas/${id}`, { metodo: 'DELETE' })
}
