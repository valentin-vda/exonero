/**
 * Las listas fijas de los formularios de perfil, y dos ayudas para armar las
 * opciones de los desplegables.
 *
 * Estan juntas aca para que las secciones (SeccionEnsena, SeccionDatos...)
 * no repitan las mismas listas, y para que cambiar un texto sea tocar un
 * solo lugar.
 */

// ---------------------------------------------------------------------------
// Catalogos: de la lista del backend a opciones de un <select>
// ---------------------------------------------------------------------------

/**
 * Las opciones de un desplegable de catalogo.
 *
 * Si los catalogos cargaron (`lista` existe): todas las opciones del catalogo.
 * Si no cargaron (P2 todavia no hizo GET /api/catalogos/todo): una sola
 * opcion, con el valor que ya estaba guardado y su nombre. Asi el usuario ve
 * lo que tiene, aunque no lo pueda cambiar.
 *
 *   opcionesDeCatalogo(catalogos?.barrios, 3, 'Pocitos')
 *   -> con catalogos: [{ valor: 1, texto: 'Cordon' }, { valor: 2, ... }, ...]
 *   -> sin catalogos: [{ valor: 3, texto: 'Pocitos' }]
 */
export function opcionesDeCatalogo(lista, idActual, nombreActual) {
  if (lista) {
    return lista.map((item) => ({ valor: item.id, texto: item.nombre }))
  }
  if (idActual) {
    return [{ valor: idActual, texto: nombreActual || `#${idActual}` }]
  }
  return []
}

/** El aviso que se muestra cuando los catalogos no cargaron. */
export const AVISO_SIN_CATALOGOS =
  'Las listas de barrios, centros, materias e idiomas todavia no estan disponibles ' +
  '(las arma P2 en GET /api/catalogos/todo). Mientras tanto ves lo que ya tenias ' +
  'guardado, pero esos campos no se pueden cambiar.'

// ---------------------------------------------------------------------------
// Listas fijas de 1j. El valor es lo que espera el backend; el texto, lo que
// ve el usuario.
// ---------------------------------------------------------------------------

/** Como da clase (perfil_profesor.modalidad). */
export const MODALIDADES = [
  { valor: 'presencial', texto: 'Solo presencial' },
  { valor: 'online', texto: 'Solo online' },
  { valor: 'ambas', texto: 'Presencial y online' },
]

/** Donde da las presenciales (perfil_profesor.lugar_clase). */
export const LUGARES = [
  { valor: 'ambos', texto: 'Espacio propio y a domicilio' },
  { valor: 'espacio_propio', texto: 'Solo espacio propio' },
  { valor: 'a_domicilio', texto: 'Solo a domicilio' },
  { valor: 'espacio_publico', texto: 'Biblioteca o espacio publico' },
]

/** Duraciones de clase, en minutos. */
export const DURACIONES = [
  { valor: 60, texto: '1 h' },
  { valor: 90, texto: '1,5 h' },
  { valor: 120, texto: '2 h' },
  { valor: 180, texto: '3 h' },
  { valor: 240, texto: '4 h' },
]

/** Descanso entre clases, en minutos. */
export const DESCANSOS = [
  { valor: 0, texto: 'Sin descanso' },
  { valor: 15, texto: '15 min' },
  { valor: 30, texto: '30 min' },
  { valor: 60, texto: '1 h' },
]

/** Aviso minimo para reservar, en horas. */
export const AVISOS = [
  { valor: 6, texto: '6 h antes' },
  { valor: 12, texto: '12 h antes' },
  { valor: 24, texto: '24 h antes' },
  { valor: 48, texto: '48 h antes' },
]

/** Individual o grupal (lo grupal esta fuera de v1: se guarda y nadie lo lee). */
export const FORMATOS = [
  { valor: 'individual', texto: 'Solo individual' },
  { valor: 'grupal', texto: 'Solo grupal' },
  { valor: 'ambos', texto: 'Individual y grupal' },
]

/** Programas que sigue. Se guarda el mismo para todas las etapas elegidas. */
export const PROGRAMAS = [
  'Plan 2006 y reformulacion 2023',
  'Solo reformulacion 2023',
  'Programa de UTU',
]

/** El texto de cada estado de la ficha. */
export const ESTADOS_FICHA = {
  borrador: 'Borrador',
  publicada: 'Publicada',
  pausada: 'Pausada',
}

// ---------------------------------------------------------------------------
// Cuentas de cobro de 1j (SeccionCuentasCobro, de P4)
// ---------------------------------------------------------------------------

/**
 * Los bancos que se pueden elegir. Es la MISMA lista que BANCOS en
 * backend/app/modulos/pagos/logica.py: el valor es el codigo que guarda el
 * backend, y el texto el nombre que se ve (el backend tambien lo devuelve,
 * como banco_nombre). Si se suma un banco alla, hay que sumarlo aca.
 */
export const BANCOS = [
  { valor: 'brou', texto: 'BROU' },
  { valor: 'santander', texto: 'Santander' },
  { valor: 'itau', texto: 'Itaú' },
  { valor: 'bbva', texto: 'BBVA' },
  { valor: 'scotiabank', texto: 'Scotiabank' },
  { valor: 'hsbc', texto: 'HSBC' },
  { valor: 'heritage', texto: 'Heritage' },
  { valor: 'bandes', texto: 'Bandes' },
]

/** La moneda de una cuenta bancaria (Mercado Pago no tiene). */
export const MONEDAS = [
  { valor: 'UYU', texto: 'Pesos uruguayos' },
  { valor: 'USD', texto: 'Dólares' },
]
