/**
 * Llamadas al modulo perfiles del backend (y la de catalogos que usan 1e y 1j).
 *
 * Igual que auth.js: una funcion por endpoint. Las pantallas llaman a estas
 * funciones y nunca a pedir() directamente, asi la forma de cada request
 * queda escrita en un solo lugar.
 *
 * Todas devuelven una Promesa: hay que esperarlas con await (o .then()).
 * Si el backend responde un error, la promesa se rechaza con un ErrorAPI que
 * trae el codigo corto (ver cliente.js), y la pantalla lo traduce con
 * mensajeDeError() de mensajes.js.
 */

import { pedir } from './cliente.js'

// ---------------------------------------------------------------------------
// Perfil del estudiante - 1e
// ---------------------------------------------------------------------------

/** GET /api/perfiles/estudiante/yo -> etapa_id, nivel, centro_id, barrio_id, ... */
export function obtenerPerfilEstudiante() {
  return pedir('/api/perfiles/estudiante/yo')
}

/** PUT /api/perfiles/estudiante/yo - reemplaza los nueve campos. */
export function guardarPerfilEstudiante(datos) {
  return pedir('/api/perfiles/estudiante/yo', { metodo: 'PUT', cuerpo: datos })
}

// ---------------------------------------------------------------------------
// Perfil del profesor - 1j. Un endpoint por seccion del formulario.
// ---------------------------------------------------------------------------

/** GET /api/perfiles/profesor/yo -> la ficha propia completa (MiFichaOut). */
export function obtenerMiFicha() {
  return pedir('/api/perfiles/profesor/yo')
}

/** PATCH .../personal - titulo_habilitante, anios_experiencia, barrio_id, latitud, longitud */
export function guardarPersonalProfesor(datos) {
  return pedir('/api/perfiles/profesor/yo/personal', { metodo: 'PATCH', cuerpo: datos })
}

/** PUT .../oferta - { materias: [ids], etapas: [{ id, programa }], idiomas: [ids] } */
export function guardarOferta(datos) {
  return pedir('/api/perfiles/profesor/yo/oferta', { metodo: 'PUT', cuerpo: datos })
}

/** PUT .../modalidad - modalidad, lugar_clase, direccion_espacio, zonas_traslado, costo_traslado */
export function guardarModalidad(datos) {
  return pedir('/api/perfiles/profesor/yo/modalidad', { metodo: 'PUT', cuerpo: datos })
}

/** PUT .../precios - precio_hora_presencial, precio_hora_online */
export function guardarPrecios(datos) {
  return pedir('/api/perfiles/profesor/yo/precios', { metodo: 'PUT', cuerpo: datos })
}

/** PUT .../reglas - duraciones, descanso, tope diario, aviso, formato y cupos */
export function guardarReglas(datos) {
  return pedir('/api/perfiles/profesor/yo/reglas', { metodo: 'PUT', cuerpo: datos })
}

/** PUT .../bio - titular, biografia, puntos_metodo */
export function guardarBio(datos) {
  return pedir('/api/perfiles/profesor/yo/bio', { metodo: 'PUT', cuerpo: datos })
}

/** POST .../fotos - { imagen_base64, epigrafe } -> { id } */
export function agregarFoto(datos) {
  return pedir('/api/perfiles/profesor/yo/fotos', { metodo: 'POST', cuerpo: datos })
}

/** PUT .../fotos/{id} - { epigrafe, orden, es_portada } */
export function editarFoto(id, datos) {
  return pedir(`/api/perfiles/profesor/yo/fotos/${id}`, { metodo: 'PUT', cuerpo: datos })
}

/** DELETE .../fotos/{id} */
export function borrarFoto(id) {
  return pedir(`/api/perfiles/profesor/yo/fotos/${id}`, { metodo: 'DELETE' })
}

/** PUT .../estado - 'borrador' | 'publicada' | 'pausada' */
export function cambiarEstadoFicha(estado) {
  return pedir('/api/perfiles/profesor/yo/estado', {
    metodo: 'PUT',
    cuerpo: { estado_ficha: estado },
  })
}

// ---------------------------------------------------------------------------
// Catalogos - el endpoint es de P2
// ---------------------------------------------------------------------------

/**
 * GET /api/catalogos/todo -> { materias, etapas, barrios, centros, idiomas }
 *
 * Llena los desplegables de 1e y 1j. El endpoint es del modulo catalogos
 * (P2); esta aca porque por ahora solo lo usan las pantallas de P1. Si P2
 * crea su propio api/catalogos.js, esta funcion se muda alla.
 *
 * Mientras P2 no lo implemente, el backend responde 500: las pantallas lo
 * atrapan y siguen funcionando con los valores que ya tenia el perfil.
 */
export function obtenerCatalogos() {
  return pedir('/api/catalogos/todo')
}
