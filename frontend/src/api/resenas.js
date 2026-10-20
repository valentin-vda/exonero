/** Llamadas al módulo de reseñas. Las usan 1b, 1i y la ficha pública 1f. */

import { pedir } from './cliente.js'

export function obtenerResenas(usuarioId, orden = 'recientes', pagina = 1) {
  const parametros = new URLSearchParams({ orden, pagina })
  return pedir(`/api/resenas/usuario/${usuarioId}?${parametros}`)
}

/** POST /api/resenas - crea la reseña propia hacia otra persona. */
export function dejarResena(datos) {
  return pedir('/api/resenas', { metodo: 'POST', cuerpo: datos })
}

/** PUT /api/resenas - reemplaza el puntaje y texto de la reseña propia. */
export function editarResena(datos) {
  return pedir('/api/resenas', { metodo: 'PUT', cuerpo: datos })
}
