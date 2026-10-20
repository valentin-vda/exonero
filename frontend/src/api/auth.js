/**
 * Llamadas al modulo cuentas del backend.
 *
 * Una funcion por endpoint. Las pantallas llaman a estas funciones y nunca a
 * pedir() directamente: asi la forma de cada request queda escrita una vez.
 */

import { pedir } from './cliente.js'

/**
 * POST /api/auth/login
 * @returns { token, expira_en, usuario: { id, nombre, rol } }
 */
export function login(correo, clave) {
  return pedir('/api/auth/login', {
    metodo: 'POST',
    cuerpo: { correo, clave },
    sinToken: true,
  })
}

/**
 * POST /api/auth/registro/estudiante  o  /profesor
 *
 * El rol va en la RUTA, no en el cuerpo: asi nadie puede darse de alta como
 * profesor mandando un campo de mas.
 *
 * @param {'estudiante'|'profesor'} rol
 * @param {object} datos  correo, clave, nombre, apellido, documento,
 *                        telefono, fecha_nacimiento
 * @returns lo mismo que el login: ya viene con el token, para entrar directo
 */
export function registrar(rol, datos) {
  return pedir(`/api/auth/registro/${rol}`, {
    metodo: 'POST',
    cuerpo: datos,
    sinToken: true,
  })
}

/** POST /api/auth/recuperar - paso 1: pedir el codigo. */
export function pedirCodigo(correo) {
  return pedir('/api/auth/recuperar', {
    metodo: 'POST',
    cuerpo: { correo },
    sinToken: true,
  })
}

/** POST /api/auth/restablecer - paso 2: fijar la clave nueva. */
export function restablecerClave(correo, codigo, claveNueva) {
  return pedir('/api/auth/restablecer', {
    metodo: 'POST',
    cuerpo: { correo, codigo, clave_nueva: claveNueva },
    sinToken: true,
  })
}

/**
 * GET /api/usuarios/yo
 * Lo llaman las diez pantallas al entrar: trae nombre, foto, rol y el contador
 * de mensajes no leidos para la cabecera.
 */
export function obtenerYo() {
  return pedir('/api/usuarios/yo')
}

// ---------------------------------------------------------------------------
// La cuenta propia. Las usan 1e y 1j: son los mismos datos para los dos roles.
// ---------------------------------------------------------------------------

/**
 * PATCH /api/usuarios/yo - nombre, apellido, documento, telefono, fecha_nacimiento.
 * Solo se cambian los campos que se mandan. El correo no se puede cambiar.
 * @returns el usuario actualizado (lo mismo que obtenerYo)
 */
export function actualizarYo(datos) {
  return pedir('/api/usuarios/yo', { metodo: 'PATCH', cuerpo: datos })
}

/** PUT /api/usuarios/yo/foto - la foto como data URL ("data:image/jpeg;base64,..."). */
export function cambiarFoto(fotoBase64) {
  return pedir('/api/usuarios/yo/foto', { metodo: 'PUT', cuerpo: { foto_base64: fotoBase64 } })
}

/** PUT /api/usuarios/yo/clave - pide la actual para poder cambiarla. */
export function cambiarClave(claveActual, claveNueva) {
  return pedir('/api/usuarios/yo/clave', {
    metodo: 'PUT',
    cuerpo: { clave_actual: claveActual, clave_nueva: claveNueva },
  })
}

/** PUT /api/usuarios/yo/tema - 'claro' | 'oscuro'. */
export function cambiarTema(tema) {
  return pedir('/api/usuarios/yo/tema', { metodo: 'PUT', cuerpo: { tema } })
}

/** DELETE /api/usuarios/yo - baja logica. Despues hay que cerrar la sesion. */
export function darmeDeBaja() {
  return pedir('/api/usuarios/yo', { metodo: 'DELETE' })
}
