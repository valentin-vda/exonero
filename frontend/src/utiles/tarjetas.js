/**
 * Funciones de las tarjetas de pago: darle forma a lo que se escribe,
 * validarlo, armar el cuerpo para el backend y mostrar una tarjeta guardada.
 *
 * Las usan el checkout (1g) y "Medios de pago" de 1e, a traves de
 * FormularioTarjeta.jsx: el formulario es el mismo en las dos pantallas, asi
 * que las reglas tambien.
 *
 * Igual que validaciones.js: esto NO reemplaza la validacion del backend
 * (TarjetaIn en pagos/esquemas.py), la duplica para avisar al instante. Si
 * cambian los limites alla, hay que cambiarlos aca.
 */

import { validarFormulario } from './validaciones.js'

/** Los cuatro puntitos que tapan el numero: "Visa •••• 4218". */
export const PUNTOS = '••••'

/** Los valores de un formulario de tarjeta vacio. Todo es texto, como en los inputs. */
export const TARJETA_VACIA = { numero: '', titular: '', vence: '', ccv: '' }

/** El valor del radio "Agregar tarjeta nueva" del checkout. Las guardadas usan su id. */
export const NUEVA = 'nueva'

// Lo que entra en el recuadrito de la marca (52 px de ancho). El backend
// deduce la marca del primer digito: Visa, Mastercard, OCA u Otra.
const MARCA_CORTA = { Mastercard: 'MC' }

/** "Mastercard" -> "MC". Las demas entran enteras. */
export function marcaCorta(marca) {
  return MARCA_CORTA[marca] || marca
}

/** Una tarjeta guardada -> "Visa •••• 4218". */
export function nombreTarjeta(tarjeta) {
  const marca = tarjeta.marca === 'Otra' ? 'Tarjeta' : tarjeta.marca
  return `${marca} ${PUNTOS} ${tarjeta.ultimos4}`
}

// ---------------------------------------------------------------------------
// Darle forma a lo que se escribe
// ---------------------------------------------------------------------------

/** Saca todo lo que no sea un digito: espacios, guiones, barras. */
export function soloDigitos(texto) {
  return texto.replace(/\D/g, '')
}

/** "4111111111111111" -> "4111 1111 1111 1111". De a cuatro y hasta 19 cifras. */
export function formatearNumero(texto) {
  return soloDigitos(texto).slice(0, 19).replace(/(\d{4})(?=\d)/g, '$1 ')
}

/**
 * "1229" -> "12/29". La barra aparece recien con el tercer digito: si se
 * agregara con el segundo, borrar hacia atras se trabaria en ella.
 */
export function formatearVence(texto) {
  const digitos = soloDigitos(texto).slice(0, 4)
  return digitos.length > 2 ? `${digitos.slice(0, 2)}/${digitos.slice(2)}` : digitos
}

/** El codigo de seguridad: solo digitos, hasta cuatro. */
export function formatearCcv(texto) {
  return soloDigitos(texto).slice(0, 4)
}

// ---------------------------------------------------------------------------
// El vencimiento
// ---------------------------------------------------------------------------

/** "12/29" -> { mes: 12, anio: 2029 }, o null si no tiene la forma MM/AA. */
export function leerVence(texto) {
  const partes = /^(\d{2})\/(\d{2})$/.exec(texto || '')
  if (!partes) return null
  // El backend quiere el anio con cuatro cifras (2029), no "29".
  return { mes: Number(partes[1]), anio: 2000 + Number(partes[2]) }
}

/**
 * true si ya vencio. Una tarjeta que dice 10/26 sirve hasta el ultimo dia de
 * octubre de 2026: vence recien cuando empieza noviembre.
 */
export function estaVencida({ mes, anio }, hoy = new Date()) {
  const anioHoy = hoy.getFullYear()
  const mesHoy = hoy.getMonth() + 1 // getMonth() cuenta desde 0
  return anio < anioHoy || (anio === anioHoy && mes < mesHoy)
}

/** Para las tarjetas guardadas, que traen vence: "MM/AA". */
export function tarjetaVencida(tarjeta) {
  const vence = leerVence(tarjeta.vence)
  return vence ? estaVencida(vence) : false
}

// ---------------------------------------------------------------------------
// Validar y mandar
// ---------------------------------------------------------------------------

/**
 * Valida el formulario de una tarjeta nueva. Devuelve { errores, hayErrores },
 * igual que validarFormulario(), con una clave por campo.
 */
export function validarTarjeta(campos) {
  const numero = soloDigitos(campos.numero)
  const vence = leerVence(campos.vence)

  return validarFormulario({
    numero: () => {
      if (!numero) return 'Escribi el numero de la tarjeta.'
      // 13 a 19: los mismos limites que TarjetaIn. Mas de 19 no se puede
      // escribir: formatearNumero() corta ahi.
      if (numero.length < 13) return 'Le faltan numeros: son entre 13 y 19.'
      return null
    },
    titular: () => (campos.titular.trim() ? null : 'Escribi el nombre como figura en la tarjeta.'),
    vence: () => {
      if (!campos.vence) return 'Escribi el vencimiento.'
      if (!vence) return 'Usa el formato MM/AA, por ejemplo 09/29.'
      if (vence.mes < 1 || vence.mes > 12) return 'El mes va del 01 al 12.'
      if (estaVencida(vence)) return 'Esta tarjeta ya vencio.'
      return null
    },
    ccv: () => (/^\d{3,4}$/.test(campos.ccv) ? null : 'Son los 3 o 4 numeros del dorso.'),
  })
}

/**
 * Lo que se escribio -> el cuerpo de POST /api/pagos/tarjetas.
 * Llamarla solo despues de validarTarjeta(): da por hecho que esta todo bien.
 */
export function tarjetaParaBackend(campos) {
  const vence = leerVence(campos.vence)
  return {
    numero: soloDigitos(campos.numero),
    titular: campos.titular.trim(),
    vence_mes: vence.mes,
    vence_anio: vence.anio,
    ccv: campos.ccv,
  }
}
