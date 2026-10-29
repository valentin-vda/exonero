/**
 * Cliente HTTP de la aplicacion.
 *
 * TODA llamada al backend pasa por aca. Nadie hace fetch() suelto en una
 * pantalla. Tres razones:
 *   1. El token se agrega en un solo lugar.
 *   2. Los errores llegan siempre con la misma forma, asi las pantallas no
 *      tienen que interpretar respuestas HTTP a mano.
 *   3. Si manana cambia la URL base o el formato del token, se toca un archivo.
 *
 * Las URLs son relativas ("/api/..."): el proxy de vite.config.js las manda a
 * localhost:8000 en desarrollo.
 */

// Donde se guarda el token. sessionStorage y no localStorage a proposito: la
// spec dice que no hay sesiones guardadas, el token vive en el frontend y
// vence solo. Con sessionStorage, cerrar la pestania es cerrar sesion.
const CLAVE_TOKEN = 'exonero_token'

export function guardarToken(token) {
  sessionStorage.setItem(CLAVE_TOKEN, token)
}

export function leerToken() {
  return sessionStorage.getItem(CLAVE_TOKEN)
}

export function borrarToken() {
  sessionStorage.removeItem(CLAVE_TOKEN)
}

// El evento que se dispara cuando el backend rechaza el token con un 401 (se
// vencio, o la cuenta ya no existe). Lo escucha ContextoAuth para cerrar la
// sesion, y RutaProtegida manda al login sola.
export const EVENTO_SESION_VENCIDA = 'exonero:sesion-vencida'

/**
 * Error de la API, con el codigo corto que devuelve el backend.
 *
 * El backend responde siempre { "detail": "codigo_corto" } en snake_case
 * (por ejemplo "credenciales_invalidas"). Ese codigo es estable; el texto que
 * ve el usuario se decide en el frontend, en mensajes.js.
 */
export class ErrorAPI extends Error {
  constructor(estado, codigo) {
    super(codigo)
    this.name = 'ErrorAPI'
    this.estado = estado   // el numero HTTP: 401, 409, ...
    this.codigo = codigo   // el string del detail
  }
}

/**
 * Hace la llamada. Uso:
 *   const datos = await pedir('/api/usuarios/yo')
 *   const r = await pedir('/api/auth/login', { metodo: 'POST', cuerpo: {...} })
 *
 * @param {string} ruta      la ruta, empezando con /api
 * @param {object} opciones  metodo, cuerpo, sinToken
 * @returns lo que devolvio el backend, ya parseado
 * @throws  {ErrorAPI} si la respuesta no fue exitosa
 */
export async function pedir(ruta, opciones = {}) {
  const { metodo = 'GET', cuerpo = null, sinToken = false } = opciones

  const cabeceras = {}
  if (cuerpo !== null) cabeceras['Content-Type'] = 'application/json'

  // El token va en Authorization, como espera app/dependencias.py.
  const token = sinToken ? null : leerToken()
  if (token) cabeceras['Authorization'] = `Bearer ${token}`

  let respuesta
  try {
    respuesta = await fetch(ruta, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo !== null ? JSON.stringify(cuerpo) : undefined,
    })
  } catch {
    // Ni siquiera llego a haber respuesta: el backend no esta levantado, o no
    // hay red. Es el error mas comun mientras se desarrolla.
    throw new ErrorAPI(0, 'sin_conexion')
  }

  // 204 = todo bien, pero no hay cuerpo que leer (por ejemplo, un DELETE).
  if (respuesta.status === 204) return null

  let datos = null
  try {
    datos = await respuesta.json()
  } catch {
    datos = null
  }

  if (!respuesta.ok) {
    // FastAPI manda el codigo en "detail". En un 422 de validacion, "detail"
    // es una lista de objetos, no un string: ahi usamos un codigo generico.
    // Un 500 ni siquiera trae JSON: el backend se rompio (por ejemplo, una
    // funcion de otro modulo que todavia levanta NotImplementedError).
    const detalle = datos && datos.detail
    let codigo = 'datos_invalidos'
    if (typeof detalle === 'string') codigo = detalle
    else if (respuesta.status >= 500) codigo = 'error_servidor'

    // Un 401 en un pedido que va con sesion es que el token ya no sirve (se
    // vencio, o lo borraron): se cierra la sesion aca, para todas las
    // pantallas a la vez. Solo si el token no cambio mientras tanto: si se
    // entro de nuevo, el nuevo no se toca. Los pedidos sinToken (el login, el
    // registro) no cierran nada.
    if (respuesta.status === 401 && !sinToken && token === leerToken()) {
      borrarToken()
      window.dispatchEvent(new Event(EVENTO_SESION_VENCIDA))
    }
    throw new ErrorAPI(respuesta.status, codigo)
  }

  return datos
}
