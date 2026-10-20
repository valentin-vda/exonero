import { pedir } from './cliente.js'

function rutaConFiltros(ruta, filtros) {
  const parametros = new URLSearchParams()

  Object.entries(filtros).forEach(([nombre, valor]) => {
    if (valor !== '' && valor !== null && valor !== undefined) {
      parametros.set(nombre, String(valor))
    }
  })

  const consulta = parametros.toString()
  return consulta ? `${ruta}?${consulta}` : ruta
}

export function buscarProfesores(filtros) {
  return pedir(rutaConFiltros('/api/busqueda/profesores', filtros), {
    sinToken: true,
  })
}

export function obtenerPinesProfesores(filtros) {
  return pedir(rutaConFiltros('/api/busqueda/profesores/mapa', filtros), {
    sinToken: true,
  })
}

/** GET /api/busqueda/cercanos - las tarjetas del carrusel de inicio. */
export function obtenerProfesoresCercanos(filtros = {}) {
  return pedir(rutaConFiltros('/api/busqueda/cercanos', filtros), {
    sinToken: true,
  })
}

/** GET /api/busqueda/mejor-puntuados - el podio de la pantalla de inicio. */
export function obtenerMejorPuntuados(filtros = {}) {
  return pedir(rutaConFiltros('/api/busqueda/mejor-puntuados', filtros), {
    sinToken: true,
  })
}
