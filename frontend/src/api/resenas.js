/**
 * Llamadas al módulo de reseñas (P3). Las usan 1b, 1i, 1e y la ficha pública 1f.
 *
 * Las reseñas son anónimas: ninguna respuesta trae el autor. El sentido
 * (alumno -> profesor o profesor -> alumno) sale del rol del token.
 *
 * Errores propios (el texto está en mensajes.js):
 *   403 sin_clases_con_esa_persona, 409 ya_resenado, 404 resena_no_existe,
 *   400 orden_invalido, 404 usuario_no_existe
 */

import { pedir } from './cliente.js'

/**
 * GET /api/resenas/usuario/{id}?orden=recientes|puntaje&pagina=1
 * -> { total, promedio, distribucion: { '5': n, ... '1': n }, resenas: [{ puntaje, texto, fecha }] }
 * De a 10 por página.
 */
export function obtenerResenas(usuarioId, orden = 'recientes', pagina = 1) {
  const parametros = new URLSearchParams({ orden, pagina })
  return pedir(`/api/resenas/usuario/${usuarioId}?${parametros}`)
}

/** GET /api/resenas/resumen/{id} -> { total, promedio, distribucion }, sin la lista. */
export function resumenResenas(usuarioId) {
  return pedir(`/api/resenas/resumen/${usuarioId}`)
}

/** POST /api/resenas - { destinatario_id, puntaje, texto } - crea la reseña propia hacia otra persona. */
export function dejarResena(datos) {
  return pedir('/api/resenas', { metodo: 'POST', cuerpo: datos })
}

/** PUT /api/resenas - reemplaza el puntaje y texto de la reseña propia. */
export function editarResena(datos) {
  return pedir('/api/resenas', { metodo: 'PUT', cuerpo: datos })
}
