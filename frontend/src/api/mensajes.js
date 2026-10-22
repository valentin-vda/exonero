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
    'Para publicar tu ficha te falta al menos una materia, el precio de cada modalidad que ofreces ' +
    'y una franja de disponibilidad (en Agenda o en la pestania Disponibilidad).',
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
  etapa_no_existe: 'Alguna de las opciones elegidas ya no existe. Recarga la pagina.',
  centro_no_existe: 'Alguna de las opciones elegidas ya no existe. Recarga la pagina.',
  rango_precio_invalido: 'El rango de precios elegido no es válido.',

  // --- Reservas y clases (1g, 1b, 1i) ---
  sin_precio: 'Este profe no da clases en esa modalidad. Elegi otra.',
  duracion_invalida: 'Este profe no da clases de esa duracion. Elegi una de las que ofrece.',
  modalidad_invalida: 'La clase tiene que ser presencial u online.',
  horario_ocupado: 'Ese horario ya no esta libre. Volve al perfil del profe y elegi otro.',
  estado_invalido: 'La clase cambio de estado mientras tanto. Recarga la pagina.',
  clase_no_existe: 'Esa clase ya no existe. Recarga la pagina.',
  profesor_no_existe: 'Ese profe no existe o pauso su ficha.',
  duracion_no_modificable:
    'Al reprogramar no se puede cambiar la duracion: el importe ya quedo fijo. Cancela y reserva de nuevo.',
  estado_no_permitido: 'Ese estado no corresponde para esta clase.',

  // --- Agenda (1i, 1j, 1f) ---
  rango_invalido: 'El rango de fechas no es valido (como mucho, 31 dias).',
  franja_invalida: 'Cada franja tiene que terminar despues de empezar.',
  franjas_superpuestas: 'Hay dos franjas del mismo dia que se pisan. Unilas o achica una.',
  bloqueo_invalido: 'El bloqueo tiene que terminar despues de empezar, y no puede estar en el pasado.',
  bloqueo_superpuesto: 'Ya tenes un bloqueo en ese horario. Borralo o elegi otro rato.',
  hay_clase_aprobada:
    'Ese rato pisa una clase confirmada. Primero cancelala o reprogramala, y despues bloquealo.',
  bloqueo_no_existe: 'Ese bloqueo ya no existe. Recarga la pagina.',
  perfil_no_existe: 'No encontramos tu perfil de profesor.',

  // --- Reseñas (1b y 1i) ---
  ya_resenado: 'Ya calificaste a esta persona. Podés editar tu reseña anterior.',
  // Lo usan resenas (hace falta una clase DICTADA) y mensajes (un profe solo
  // le escribe a un alumno con el que tiene alguna clase).
  sin_clases_con_esa_persona: 'Para eso tienen que haber tenido una clase juntos.',
  resena_no_existe: 'Todavia no calificaste a esta persona. Recarga la pagina.',
  orden_invalido: 'Ese orden no existe. Elegi recientes o puntaje.',
  usuario_no_existe: 'Esa persona ya no existe.',

  // --- Mensajes (1h) ---
  hilo_no_existe: 'Esa conversacion ya no existe. Volve a la bandeja.',
  mensaje_vacio: 'El mensaje esta vacio.',
  estudiante_no_existe: 'Ese alumno ya no existe.',

  // --- Panel del profesor (1d) ---
  periodo_invalido: 'Ese periodo no existe. Elegi mes, trimestre o anio.',
  agrupacion_invalida: 'Esa agrupacion no existe. Elegi semana, mes o anio.',

  // --- Pagos y tarjetas (1g, 1e) ---
  cobro_no_existe: 'No encontramos el pago de esa clase. Recarga la pagina.',
  cobro_rechazado: 'La tarjeta rechazo el pago. Proba con otra.',
  tarjeta_vencida: 'Esa tarjeta esta vencida. Usa otra o agrega una nueva.',
  tarjeta_invalida: 'El numero de tarjeta no es valido.',
  tarjeta_no_existe: 'Esa tarjeta ya no esta guardada. Recarga la pagina.',

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
