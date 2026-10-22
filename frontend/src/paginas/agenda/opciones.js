/**
 * Las listas fijas de la agenda del profesor (1i) y del editor de franjas
 * (que tambien usa 1j).
 *
 * Igual que panel/opciones.js: el valor es lo que espera el backend y el
 * texto es lo que ve el usuario.
 */

/**
 * Los dias en el orden en que se dibujan (lunes primero, como en el mockup).
 * `valor` es dia_semana del backend: 0 = domingo ... 6 = sabado, el mismo
 * criterio que Date.getDay().
 */
export const DIAS = [
  { valor: 1, texto: 'Lunes', corto: 'lun' },
  { valor: 2, texto: 'Martes', corto: 'mar' },
  { valor: 3, texto: 'Miercoles', corto: 'mie' },
  { valor: 4, texto: 'Jueves', corto: 'jue' },
  { valor: 5, texto: 'Viernes', corto: 'vie' },
  { valor: 6, texto: 'Sabado', corto: 'sab' },
  { valor: 0, texto: 'Domingo', corto: 'dom' },
]

/** La modalidad de una franja: a diferencia de una clase, puede ser "ambas". */
export const MODALIDADES_FRANJA = [
  { valor: 'ambas', texto: 'Presencial y online' },
  { valor: 'presencial', texto: 'Solo presencial' },
  { valor: 'online', texto: 'Solo online' },
]

/**
 * Lo que dice la pantalla cuando POST /agenda/verificar responde
 * { libre: false, motivo }. Lo usa el reprogramar de 1i (DetalleClase).
 */
export const MOTIVOS_NO_LIBRE = {
  ocupado: 'Ya tenes una clase confirmada en ese horario.',
  bloqueado: 'Ese horario esta bloqueado en tu agenda.',
  fuera_de_franja: 'Ese horario esta fuera de tu disponibilidad.',
  aviso_minimo: 'Es demasiado sobre la hora: no llega al aviso minimo que pediste.',
  tope_diario: 'Ese dia ya llegaste al maximo de clases que configuraste.',
}

/** Lo mismo, dicho para el alumno que reprograma desde 1b. */
export const MOTIVOS_NO_LIBRE_ALUMNO = {
  ocupado: 'El profe ya tiene otra clase confirmada en ese horario.',
  bloqueado: 'El profe bloqueo ese horario en su agenda.',
  fuera_de_franja: 'El profe no da clases en ese horario.',
  aviso_minimo: 'Es demasiado sobre la hora: el profe pide mas aviso.',
  tope_diario: 'Ese dia el profe ya llego a su maximo de clases.',
}

/** Las pestanias de abajo del calendario. El id es tambien el #hash de la URL. */
export const PESTANIAS = [
  { id: 'disponibilidad', texto: 'Disponibilidad' },
  { id: 'bloqueos', texto: 'Bloqueos' },
  { id: 'alumnos', texto: 'Mis alumnos' },
]
