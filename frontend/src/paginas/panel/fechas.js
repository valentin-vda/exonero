/**
 * Fechas del panel del profesor (1d): "hoy", "en 40 min", "6 h 30 min" y los
 * tramos de los graficos (semanas, meses, anios).
 *
 * Estan aca y no en utiles/formato.js porque por ahora solo las usa 1d. Si
 * otra pantalla las necesita, se mudan alla.
 *
 * Todo se calcula en la zona de Montevideo, la misma que usa el backend
 * (ZONA_HORARIA en app/config.py): "hoy" es el hoy de Montevideo aunque la
 * computadora este configurada en otra zona.
 *
 * Los dias van como texto 'AAAA-MM-DD', que es como los manda el backend en
 * las etiquetas de los graficos. Para sumar o restar dias se pasan a una fecha
 * a las 00:00 UTC: asi no hay cambios de hora que corran un dia.
 */

const ZONA = 'America/Montevideo'

// Cuantos tramos tiene cada grafico. Es la ventana que devuelve el backend.
const VENTANA = { semana: 10, mes: 12, anio: 5 }

/** Un instante (Date o texto ISO) -> 'AAAA-MM-DD' del dia que era en Montevideo. */
export function diaEnMontevideo(instante) {
  // en-CA es el formato que escribe el anio primero: "2026-10-20".
  return new Date(instante).toLocaleDateString('en-CA', { timeZone: ZONA })
}

/** La fecha de hoy en Montevideo: '2026-10-20'. */
export function hoy() {
  return diaEnMontevideo(new Date())
}

/** 'AAAA-MM-DD' -> Date a las 00:00 UTC de ese dia. */
function aFecha(dia) {
  const [anio, mes, numero] = dia.split('-').map(Number)
  return new Date(Date.UTC(anio, mes - 1, numero))
}

/** Lo contrario: Date en UTC -> 'AAAA-MM-DD'. */
function aDia(fecha) {
  return fecha.toISOString().slice(0, 10)
}

/** Cuantos dias hay del primero al segundo ('2026-10-20', '2026-10-21' -> 1). */
function diasEntre(desde, hasta) {
  return Math.round((aFecha(hasta) - aFecha(desde)) / 86400000)
}

/** 'AAAA-MM-DD' -> "jueves 3 de septiembre". */
export function diaLargo(dia) {
  // El navegador escribe "jueves, 3 de septiembre": la coma se saca, como en el mockup.
  return aFecha(dia)
    .toLocaleDateString('es-UY', { weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC' })
    .replace(',', '')
}

/** Un instante + minutos -> el instante del final, en ISO (para hora()). */
export function finDe(inicioIso, duracionMin) {
  return new Date(new Date(inicioIso).getTime() + duracionMin * 60000).toISOString()
}

/** 390 -> "6 h 30 min", 60 -> "1 h", 45 -> "45 min". */
export function duracion(minutos) {
  const horas = Math.floor(minutos / 60)
  const resto = minutos % 60
  if (!horas) return `${resto} min`
  return resto ? `${horas} h ${resto} min` : `${horas} h`
}

/**
 * "Hoy", "Manana" o "Jueves 22 de octubre" para el dia de una clase.
 * Con mayuscula: va al principio del renglon.
 */
export function cuandoEs(inicioIso) {
  const dias = diasEntre(hoy(), diaEnMontevideo(inicioIso))
  if (dias === 0) return 'Hoy'
  if (dias === 1) return 'Manana'
  const texto = diaLargo(diaEnMontevideo(inicioIso))
  return texto[0].toUpperCase() + texto.slice(1)
}

/**
 * La cuenta regresiva de la proxima clase: "en 40 min", "en 2 h 15 min",
 * "manana" o "el jueves 22 de octubre".
 *
 * Los minutos los calcula el backend (minutos_restantes). Aca solo se decide
 * como decirlo: en minutos si es hoy, y con el dia si es otro.
 */
export function cuantoFalta(minutosRestantes, inicioIso) {
  if (minutosRestantes <= 0) return 'ahora'
  const dias = diasEntre(hoy(), diaEnMontevideo(inicioIso))
  if (dias <= 0) return `en ${duracion(minutosRestantes)}`
  if (dias === 1) return 'manana'
  return `el ${diaLargo(diaEnMontevideo(inicioIso))}`
}

// ---------------------------------------------------------------------------
// Los tramos de los graficos
// ---------------------------------------------------------------------------

/**
 * El inicio de cada tramo de la ventana, del mas viejo al actual.
 *   semana -> los lunes de las ultimas 10 semanas
 *   mes    -> el dia 1 de los ultimos 12 meses
 *   anio   -> el 1 de enero de los ultimos 5 anios
 *
 * Es la misma cuenta que hace el backend para armar la etiqueta de cada tramo
 * (el inicio del tramo, 'AAAA-MM-DD'). Hace falta porque el backend no manda
 * los tramos sin clases: el grafico los completa con 0.
 */
export function tramos(agrupar) {
  const hoyFecha = aFecha(hoy())
  const anio = hoyFecha.getUTCFullYear()
  const mes = hoyFecha.getUTCMonth()
  const cantidad = VENTANA[agrupar]
  const lista = []

  for (let atras = cantidad - 1; atras >= 0; atras--) {
    if (agrupar === 'semana') {
      // getUTCDay(): 0 es domingo. (dia + 6) % 7 son los dias desde el lunes.
      const desdeElLunes = (hoyFecha.getUTCDay() + 6) % 7
      const lunes = new Date(hoyFecha)
      lunes.setUTCDate(hoyFecha.getUTCDate() - desdeElLunes - 7 * atras)
      lista.push(aDia(lunes))
    } else if (agrupar === 'mes') {
      // Date.UTC acepta meses negativos: (2026, -1) es diciembre de 2025.
      lista.push(aDia(new Date(Date.UTC(anio, mes - atras, 1))))
    } else {
      lista.push(aDia(new Date(Date.UTC(anio - atras, 0, 1))))
    }
  }
  return lista
}

/**
 * Los tramos de la ventana mas los que mando el backend, sin repetir y en
 * orden. Normalmente son los mismos; si el backend manda alguno que la cuenta
 * de aca no tenia, igual se dibuja (mejor una barra de mas que un dato perdido).
 * Como son 'AAAA-MM-DD', ordenarlos como texto es ordenarlos por fecha.
 */
export function conTodosLosTramos(agrupar, recibidos) {
  return [...new Set([...tramos(agrupar), ...recibidos])].sort()
}

/** "octubre": el mes en curso, en Montevideo. */
export function mesActual() {
  return new Date().toLocaleDateString('es-UY', { month: 'long', timeZone: ZONA })
}

/**
 * Las etiquetas de un tramo: la corta va debajo de la barra y la larga en el
 * cartelito del mouse y en la tabla para lectores de pantalla.
 *   semana -> "S3" (la tercera de la ventana)  y "semana del 12 de octubre"
 *   mes    -> "oct"                            y "octubre de 2026"
 *   anio   -> "2026"                           y "2026"
 */
export function etiquetas(dia, agrupar, posicion) {
  const fecha = aFecha(dia)
  if (agrupar === 'semana') {
    const desde = fecha.toLocaleDateString('es-UY', { day: 'numeric', month: 'long', timeZone: 'UTC' })
    return { corta: `S${posicion + 1}`, larga: `semana del ${desde}` }
  }
  if (agrupar === 'mes') {
    // Segun el navegador, el mes corto viene como "oct" o "oct.": se le saca el punto.
    const corta = fecha.toLocaleDateString('es-UY', { month: 'short', timeZone: 'UTC' }).replace('.', '')
    const larga = fecha.toLocaleDateString('es-UY', { month: 'long', year: 'numeric', timeZone: 'UTC' })
    return { corta, larga }
  }
  const anio = String(fecha.getUTCFullYear())
  return { corta: anio, larga: anio }
}

/** "esta semana", "este mes", "este anio": para las frases de los graficos. */
export const ESTE_TRAMO = { semana: 'esta semana', mes: 'este mes', anio: 'este anio' }
