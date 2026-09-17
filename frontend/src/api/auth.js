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
