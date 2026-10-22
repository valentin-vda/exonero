/**
 * Llamadas al modulo mensajeria del backend (P3): el chat de 1h y el
 * contador de no leidos de la cabecera.
 *
 * Ojo con el nombre: mensajes.js NO es esto, es la tabla de textos de error.
 *
 * Lo usan:
 *   1h Mensajes            bandeja(), mensajesDelHilo(), enviarMensaje()
 *   Layout (cabecera)      noLeidos(), cada diez segundos (useNoLeidos.js)
 *   BotonMensaje (1a, 1b, 1d, 1f, 1i)  abrirHilo()
 *
 * Errores propios (el texto esta en mensajes.js):
 *   400 datos_invalidos, 400 mensaje_vacio, 403 sin_clases_con_esa_persona,
 *   404 profesor_no_existe, 404 estudiante_no_existe, 404 hilo_no_existe
 */

import { pedir } from './cliente.js'

/** GET /api/mensajes/no-leidos -> { no_leidos } */
export function noLeidos() {
  return pedir('/api/mensajes/no-leidos')
}

/**
 * GET /api/mensajes/hilos?q=... -> [{ id, contraparte, ultimo_mensaje,
 * ultimo_mensaje_el, no_leidos }], el de actividad mas reciente primero.
 * contraparte trae materias si es profe, o etapa y centro si es alumno.
 */
export function bandeja(q = '') {
  const consulta = q.trim() ? `?${new URLSearchParams({ q: q.trim() })}` : ''
  return pedir(`/api/mensajes/hilos${consulta}`)
}

/**
 * POST /api/mensajes/hilos - abre (o devuelve, si ya existe) la conversacion
 * con otra persona. El alumno manda { profesor_id }, el profesor
 * { estudiante_id } (solo de un alumno con el que tiene clase). -> HiloOut
 */
export function abrirHilo(datos) {
  return pedir('/api/mensajes/hilos', { metodo: 'POST', cuerpo: datos })
}

/**
 * GET /api/mensajes/hilos/{id}/mensajes?antes=&limite= -> [{ id, autor_id,
 * contenido, enviado_el }] en orden cronologico (el mas viejo primero).
 * ABRIR ES LEER: este GET marca como leidos los mensajes del otro.
 * `antes` es el id del mensaje mas viejo que ya se tiene ("Cargar anteriores").
 */
export function mensajesDelHilo(hiloId, antes = null, limite = 30) {
  const parametros = new URLSearchParams({ limite })
  if (antes) parametros.set('antes', antes)
  return pedir(`/api/mensajes/hilos/${hiloId}/mensajes?${parametros}`)
}

/** POST /api/mensajes/hilos/{id}/mensajes - { texto } -> el mensaje creado. */
export function enviarMensaje(hiloId, texto) {
  return pedir(`/api/mensajes/hilos/${hiloId}/mensajes`, { metodo: 'POST', cuerpo: { texto } })
}
