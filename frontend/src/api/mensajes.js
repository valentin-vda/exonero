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

  // --- Perfil: datos de la cuenta (1e y 1j) ---
  nombre_requerido: 'El nombre no puede quedar vacio.',
  apellido_requerido: 'El apellido no puede quedar vacio.',
  fecha_invalida: 'La fecha de nacimiento no es valida.',
  clave_actual_incorrecta: 'La contrasena actual no es correcta.',
  foto_invalida: 'Ese archivo no es una imagen que podamos usar. Proba con un JPG o PNG.',
  foto_muy_grande: 'La imagen es demasiado pesada.',

  // --- Perfil del estudiante (1e) ---
  adulto_responsable_requerido:
    'Como sos menor de edad, completa el nombre y el telefono de un adulto responsable.',

  // --- Perfil del profesor (1j) ---
  ficha_incompleta:
    'Para publicar tu ficha te falta al menos una materia y el precio de cada modalidad que ofreces.',
  duraciones_incoherentes: 'La duracion maxima no puede ser menor que la minima.',
  duracion_fuera_de_rango: 'Las duraciones que ofreces tienen que estar entre la minima y la maxima.',
  cupos_incoherentes: 'El minimo de alumnos no puede ser mayor que el maximo.',
  maximo_fotos: 'Ya tenes las 4 fotos. Quita una para poder subir otra.',
  foto_no_existe: 'Esa foto ya no existe. Recarga la pagina.',

  // --- Un id de catalogo que no existe (barrio, materia, ...) ---
  barrio_no_existe: 'Alguna de las opciones elegidas ya no existe. Recarga la pagina.',
  materia_no_existe: 'Alguna de las opciones elegidas ya no existe. Recarga la pagina.',
  idioma_no_existe: 'Alguna de las opciones elegidas ya no existe. Recarga la pagina.',
  etapa_educativa_no_existe: 'Alguna de las opciones elegidas ya no existe. Recarga la pagina.',
  centro_educativo_no_existe: 'Alguna de las opciones elegidas ya no existe. Recarga la pagina.',

  // --- Generales ---
  datos_invalidos: 'Revisa los datos: hay algo que no esta bien.',
  error_servidor:
    'El servidor tuvo un problema. Si es una parte de la app que todavia no esta hecha, es normal.',
}

/**
 * Devuelve el texto para mostrarle al usuario.
 * Si el codigo no esta en la lista, se muestra un mensaje generico en vez del
 * codigo crudo: "correo_ya_registrado" no le dice nada a nadie.
 */
export function mensajeDeError(codigo) {
  return MENSAJES[codigo] || 'Algo salio mal. Intenta de nuevo en un momento.'
}
