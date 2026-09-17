/**
 * Traduccion de los codigos de error del backend a texto para el usuario.
 *
 * El backend devuelve codigos cortos y estables en snake_case. El texto en
 * espanol vive aca, en el frontend, por dos motivos: se puede cambiar la
 * redaccion sin tocar el backend, y el dia que haya otro idioma es un archivo
 * mas y nada mas.
 */

const MENSAJES = {
  // --- Conexion ---
  sin_conexion:
    'No se pudo conectar con el servidor. Fijate que el backend este levantado en el puerto 8000.',

  // --- Login y registro ---
  credenciales_invalidas: 'El correo o la contrasena no son correctos.',
  correo_ya_registrado: 'Ya hay una cuenta con ese correo.',
  documento_ya_registrado: 'Ya hay una cuenta con ese documento.',
  codigo_invalido: 'El codigo no es valido o ya vencio.',

  // --- Sesion ---
  sin_token: 'Tu sesion vencio. Volve a entrar.',
  no_es_tuyo: 'No tenes permiso para hacer eso.',

  // --- Generales ---
  datos_invalidos: 'Revisa los datos: hay algo que no esta bien.',
}

/**
 * Devuelve el texto para mostrarle al usuario.
 * Si el codigo no esta en la lista, se muestra un mensaje generico en vez del
 * codigo crudo: "correo_ya_registrado" no le dice nada a nadie.
 */
export function mensajeDeError(codigo) {
  return MENSAJES[codigo] || 'Algo salio mal. Intenta de nuevo en un momento.'
}
