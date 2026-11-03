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
  sin_conexion: 'No se pudo conectar con el servidor. Revisa tu conexion e intenta de nuevo en un momento.',

  // --- Login y registro ---
  credenciales_invalidas: 'El correo o la contraseña no son correctos.',
  correo_ya_registrado: 'Ya hay una cuenta con ese correo.',
  documento_ya_registrado: 'Ya hay una cuenta con ese documento.',
  codigo_invalido: 'El código no es válido o ya venció.',

  // --- Sesion ---
  sin_token: 'Tu sesión venció. Volvé a entrar.',
  no_es_tuyo: 'No tenés permiso para hacer eso.',

  // --- Perfil: datos de la cuenta (1e y 1j) ---
  nombre_requerido: 'El nombre no puede quedar vacío.',
  apellido_requerido: 'El apellido no puede quedar vacío.',
  fecha_invalida: 'La fecha de nacimiento no es valida.',
  fecha_nacimiento_no_modificable: 'La fecha de nacimiento no se cambia desde el perfil porque determina el consentimiento parental.',
  clave_actual_incorrecta: 'La contraseña actual no es correcta.',
  foto_invalida: 'Ese archivo no es una imagen que podamos usar. Proba con un JPG o PNG.',
  foto_muy_grande: 'La imagen es demasiado pesada.',

  // --- Perfil del estudiante (1e) ---
  adulto_responsable_requerido:
    'Como sos menor de edad, completá el nombre y el teléfono de un adulto responsable.',

  // --- Perfil del profesor (1j) ---
  ficha_incompleta:
    'Para publicar tu ficha te falta al menos una materia, el precio de cada modalidad que ofrecés ' +
    'y una franja de disponibilidad (en Agenda o en la pestaña Disponibilidad).',
  duraciones_incoherentes: 'La duración máxima no puede ser menor que la mínima.',
  duracion_fuera_de_rango: 'Las duraciones que ofrecés tienen que estar entre la mínima y la máxima.',
  cupos_incoherentes: 'El mínimo de alumnos no puede ser mayor que el máximo.',
  maximo_fotos: 'Ya tenés las 4 fotos. Quitá una para poder subir otra.',
  foto_no_existe: 'Esa foto ya no existe. Recargá la página.',

  // --- Un id de catalogo que no existe (barrio, materia, ...) ---
  barrio_no_existe: 'Alguna de las opciones elegidas ya no existe. Recargá la página.',
  materia_no_existe: 'Alguna de las opciones elegidas ya no existe. Recargá la página.',
  idioma_no_existe: 'Alguna de las opciones elegidas ya no existe. Recargá la página.',
  etapa_educativa_no_existe: 'Alguna de las opciones elegidas ya no existe. Recargá la página.',
  centro_educativo_no_existe: 'Alguna de las opciones elegidas ya no existe. Recargá la página.',
  etapa_no_existe: 'Alguna de las opciones elegidas ya no existe. Recargá la página.',
  centro_no_existe: 'Alguna de las opciones elegidas ya no existe. Recargá la página.',
  rango_precio_invalido: 'El rango de precios elegido no es válido.',

  // --- Reservas y clases (1g, 1b, 1i) ---
  sin_precio: 'Este profe no da clases en esa modalidad. Elegí otra.',
  duracion_invalida: 'Este profe no da clases de esa duración. Elegí una de las que ofrece.',
  modalidad_invalida: 'La clase tiene que ser presencial u online.',
  horario_ocupado: 'Ese horario ya no esta libre. Volve al perfil del profe y elegi otro.',
  // No lo manda el backend: es horario_ocupado dicho para el profe que
  // aprueba una solicitud (Solicitudes.jsx y DetalleClase.jsx). El de arriba
  // es para el alumno que reserva.
  horario_ocupado_al_aprobar:
    'No se puede aprobar: ese horario se cruza con otra clase que ya aprobaste o con un bloqueo de tu ' +
    'agenda. Rechaza esta solicitud, o libera ese rato (mueve o cancela la otra clase, o borra el bloqueo) ' +
    'y volve a aprobarla.',
  estado_invalido: 'La clase cambio de estado mientras tanto. Recarga la pagina.',
  clase_no_existe: 'Esa clase ya no existe. Recarga la pagina.',
  profesor_no_existe: 'Ese profe no existe o pauso su ficha.',
  duracion_no_modificable:
    'Al reprogramar no se puede cambiar la duración: el importe ya quedó fijo. Cancelá y reservá de nuevo.',
  estado_no_permitido: 'Ese estado no corresponde para esta clase.',

  // --- Agenda (1i, 1j, 1f) ---
  rango_invalido: 'El rango de fechas no es válido (como mucho, 31 días).',
  franja_invalida: 'Cada franja tiene que terminar después de empezar.',
  franjas_superpuestas: 'Hay dos franjas del mismo día que se pisan. Unilas o achicá una.',
  bloqueo_invalido: 'El bloqueo tiene que terminar después de empezar, y no puede estar en el pasado.',
  bloqueo_superpuesto: 'Ya tenés un bloqueo en ese horario. Borralo o elegí otro rato.',
  hay_clase_aprobada:
    'Ese rato pisa una clase confirmada. Primero cancelala o reprogramala, y después bloquealo.',
  bloqueo_no_existe: 'Ese bloqueo ya no existe. Recargá la página.',
  perfil_no_existe: 'No encontramos tu perfil de profesor.',

  // --- Reseñas (1b y 1i) ---
  ya_resenado: 'Ya calificaste a esta persona. Podés editar tu reseña anterior.',
  // Lo usan resenas (hace falta una clase DICTADA) y mensajes (un profe solo
  // le escribe a un alumno con el que tiene alguna clase).
  sin_clases_con_esa_persona: 'Para eso tienen que haber tenido una clase juntos.',
  resena_no_existe: 'Todavía no calificaste a esta persona. Recargá la página.',
  orden_invalido: 'Ese orden no existe. Elegí recientes o puntaje.',
  usuario_no_existe: 'Esa persona ya no existe.',

  // --- Mensajes (1h) ---
  hilo_no_existe: 'Esa conversación ya no existe. Volvé a la bandeja.',
  mensaje_vacio: 'El mensaje está vacío.',
  estudiante_no_existe: 'Ese alumno ya no existe.',

  // --- Panel del profesor (1d) ---
  periodo_invalido: 'Ese período no existe. Elegí mes, trimestre o año.',
  agrupacion_invalida: 'Esa agrupación no existe. Elegí semana, mes o año.',

  // --- Pagos y tarjetas (1g, 1e) ---
  cobro_no_existe: 'No encontramos el pago de esa clase. Recargá la página.',
  cobro_rechazado: 'La tarjeta rechazo el pago. Proba con otra.',
  tarjeta_vencida: 'Esa tarjeta está vencida. Usá otra o agregá una nueva.',
  tarjeta_invalida: 'El número de tarjeta no es válido.',
  solo_tarjeta_prueba: 'Este prototipo solo acepta las tarjetas ficticias 4111 1111 1111 1111 y 5555 5555 5555 4444.',
  tarjeta_no_existe: 'Esa tarjeta ya no está guardada. Recargá la página.',

  // --- Cuentas de cobro del profesor (1j) ---
  cuenta_invalida:
    'Revisá los datos de la cuenta: el número va solo con dígitos (entre 6 y 20), y hacen falta la moneda y el titular.',
  banco_no_existe: 'Ese banco no está en la lista. Elegí uno de los que aparecen.',
  correo_invalido: 'Ese correo de Mercado Pago no parece válido.',
  cuenta_no_existe: 'Esa cuenta de cobro ya no está guardada. Recargá la página.',
  cuenta_repetida: 'Ya tenés esa cuenta guardada.',
  correo_no_disponible: 'El correo de prueba no está disponible. Levantá Mailpit con Docker Compose.',
  enlace_parental_invalido: 'El enlace parental no es válido, ya fue usado o venció.',
  correo_adulto_requerido: 'Para un estudiante menor necesitamos el correo de un adulto responsable.',
  profesor_debe_ser_mayor: 'Las cuentas de profesor requieren ser mayor de 18 años.',
  aviso_privacidad_desactualizado: 'El aviso de privacidad cambió. Recargá la página y volvé a aceptarlo.',

  // --- Generales ---
  demasiados_intentos: 'Hiciste demasiados intentos. Esperá un minuto y probá de nuevo.',
  datos_invalidos: 'Revisá los datos: hay algo que no está bien.',
  error_servidor:
    'El servidor tuvo un problema. Si es una parte de la app que todavía no está hecha, es normal.',
}

/**
 * Devuelve el texto para mostrarle al usuario.
 * Si el codigo no esta en la lista, se muestra un mensaje generico en vez del
 * codigo crudo: "correo_ya_registrado" no le dice nada a nadie.
 */
export function mensajeDeError(codigo) {
  return MENSAJES[codigo] || 'Algo salió mal. Intentá de nuevo en un momento.'
}
