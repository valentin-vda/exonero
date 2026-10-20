/**
 * Las listas fijas del panel del profesor (1d): las opciones de los tres
 * selectores, los textos de cada periodo y como se muestra cada estado de una
 * clase.
 *
 * Igual que perfil/opciones.js: el valor es lo que espera el backend y el
 * texto es lo que ve el usuario. Cambiar un texto es tocar un solo lugar.
 */

// ---------------------------------------------------------------------------
// Los selectores
// ---------------------------------------------------------------------------

/** Indicadores: el periodo calendario en curso contra el anterior. */
export const PERIODOS = [
  { valor: 'mes', texto: 'Mes' },
  { valor: 'trimestre', texto: 'Trimestre' },
  { valor: 'anio', texto: 'Anio' },
]

/** Grafico de ingresos: de a cuanto se agrupa cada barra. */
export const AGRUPAR_INGRESOS = [
  { valor: 'semana', texto: 'Semana' },
  { valor: 'mes', texto: 'Mes' },
  { valor: 'anio', texto: 'Anio' },
]

/** Grafico de reservas: la ventana es de 10 semanas, 12 meses o 5 anios. */
export const AGRUPAR_RESERVAS = [
  { valor: 'semana', texto: '10 semanas' },
  { valor: 'mes', texto: 'Mes' },
  { valor: 'anio', texto: 'Anio' },
]

/** El resumen de cada grafico para el lector de pantalla: "Reservas por semana, ultimas 10 semanas". */
export const POR_TRAMO = {
  semana: 'por semana, ultimas 10 semanas',
  mes: 'por mes, ultimos 12 meses',
  anio: 'por anio, ultimos 5 anios',
}

/** "Ingresos del mes", "cobrado este trimestre", "+6 % que el anio pasado". */
export const DEL_PERIODO = { mes: 'del mes', trimestre: 'del trimestre', anio: 'del anio' }
export const ESTE_PERIODO = { mes: 'este mes', trimestre: 'este trimestre', anio: 'este anio' }
export const PERIODO_PASADO = { mes: 'el mes pasado', trimestre: 'el trimestre pasado', anio: 'el anio pasado' }

// ---------------------------------------------------------------------------
// Las clases
// ---------------------------------------------------------------------------

/**
 * La etiqueta de cada estado en la tabla de "Reservas de hoy". Los nombres
 * son los del mockup: para el profesor, "aprobada" es una clase confirmada y
 * "pendiente" una que todavia tiene que confirmar.
 */
export const ESTADOS_CLASE = {
  dictada: { texto: 'Dictada', clase: 'tag-neutral' },
  aprobada: { texto: 'Confirmada', clase: 'tag-accent-2' },
  pendiente: { texto: 'A confirmar', clase: 'tag-outline' },
  cancelada: { texto: 'Cancelada', clase: 'tag-neutral' },
  no_asistida: { texto: 'No asistio', clase: 'tag-neutral' },
}

/** La modalidad de UNA clase: es presencial u online, nunca "ambas". */
export const MODALIDAD_CLASE = { presencial: 'Presencial', online: 'Online' }

/**
 * Las series del grafico apilado de "Reservas en el tiempo", de abajo hacia
 * arriba. Cancelada y no_asistida van juntas: para mirar el volumen de
 * reservas, las dos son "no se dio". La clase de CSS elige el color
 * (panel.css).
 */
export const SERIES_RESERVAS = [
  { id: 'dictada', texto: 'Dictadas', clase: 'serie-dictada', estados: ['dictada'] },
  { id: 'aprobada', texto: 'Confirmadas', clase: 'serie-confirmada', estados: ['aprobada'] },
  { id: 'pendiente', texto: 'A confirmar', clase: 'serie-pendiente', estados: ['pendiente'] },
  { id: 'no_se_dio', texto: 'No se dieron', clase: 'serie-no-se-dio', estados: ['cancelada', 'no_asistida'] },
]
