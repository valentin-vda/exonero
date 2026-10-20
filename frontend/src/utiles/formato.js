/**
 * Funciones chicas para mostrar datos: iniciales, fechas, puntajes.
 *
 * Estan aca y no en cada pantalla para que "4,8" o "marzo de 2026" se escriban
 * igual en toda la app.
 *
 * Los caracteres especiales (el punto medio, la estrella, la cruz) van como
 * codigo \u... para que los archivos de codigo sigan siendo texto sin acentos
 * (ver "Los acentos y las enies" en la documentacion).
 */

/** El separador de las cabeceras: "Bachillerato · Liceo Bauza · Cordon". */
export const SEPARADOR = ' · '

/** La estrella de los puntajes. */
export const ESTRELLA = '★'

/** La cruz de "quitar" en las etiquetas. */
export const CRUZ = '×'

/** "Martina Silva" -> "MS". Para el circulito del avatar cuando no hay foto. */
export function iniciales(persona) {
  const n = (persona?.nombre || '').trim()[0] || ''
  const a = (persona?.apellido || '').trim()[0] || ''
  return (n + a).toUpperCase() || '?'
}

/** "2026-03-14T10:00:00Z" -> "marzo de 2026". */
export function mesYAnio(fechaIso) {
  if (!fechaIso) return ''
  return new Date(fechaIso).toLocaleDateString('es-UY', { month: 'long', year: 'numeric' })
}

/** 4.8 -> "4,8". El backend manda los decimales como texto ("4.80") o numero. */
export function puntaje(valor) {
  return Number(valor || 0).toLocaleString('es-UY', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
}

/**
 * Une las partes que existan con el separador, salteando las vacias.
 *   unir(['Bachillerato', null, 'Cordon']) -> "Bachillerato · Cordon"
 */
export function unir(partes) {
  return partes.filter(Boolean).join(SEPARADOR)
}

/**
 * Texto de un input numerico -> numero, o null si esta vacio.
 *
 * Los inputs siempre guardan TEXTO en el estado (aunque sean type="number"):
 * "700", "" ... Al mandar al backend hay que convertirlo, y vacio quiere decir
 * "sin valor" (null), no cero.
 */
export function aNumero(texto) {
  if (texto === '' || texto === null || texto === undefined) return null
  const numero = Number(texto)
  return Number.isNaN(numero) ? null : numero
}

/** Lo contrario: numero (o null) -> texto para el input. */
export function aTexto(valor) {
  return valor === null || valor === undefined ? '' : String(valor)
}
