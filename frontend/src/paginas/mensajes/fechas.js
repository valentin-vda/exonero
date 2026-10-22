/**
 * Las fechas del chat (1h): "hace 5 min", "ayer", "12 oct." en la bandeja, y
 * los separadores por dia de la conversacion ("Hoy", "Ayer", "Jueves 15 de
 * octubre").
 *
 * Todo en la zona de Montevideo, como el resto de la app (panel/fechas.js).
 */

import { diaEnMontevideo, hoy, sumarDias } from '../panel/fechas.js'

const ZONA = 'America/Montevideo'

/** La hora o el dia de la ultima actividad, para la bandeja. */
export function cuando(instante) {
  const minutos = Math.floor((Date.now() - new Date(instante).getTime()) / 60000)
  if (minutos < 1) return 'ahora'
  if (minutos < 60) return `hace ${minutos} min`
  const dia = diaEnMontevideo(instante)
  if (dia === hoy()) return new Date(instante).toLocaleTimeString('es-UY', { hour: '2-digit', minute: '2-digit', hourCycle: 'h23', timeZone: ZONA })
  if (dia === sumarDias(hoy(), -1)) return 'ayer'
  return new Date(instante).toLocaleDateString('es-UY', { day: 'numeric', month: 'short', timeZone: ZONA })
}

/** El separador de un dia dentro de la conversacion. */
export function separadorDeDia(dia) {
  if (dia === hoy()) return 'Hoy'
  if (dia === sumarDias(hoy(), -1)) return 'Ayer'
  const texto = new Date(`${dia}T12:00:00Z`).toLocaleDateString('es-UY', {
    weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC',
  }).replace(',', '')
  return texto.charAt(0).toUpperCase() + texto.slice(1)
}
