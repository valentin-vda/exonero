/**
 * Validaciones del lado del cliente.
 *
 * Ojo: esto NO reemplaza la validacion del backend, la duplica a proposito.
 * El backend valida porque es el unico que no se puede saltear; el frontend
 * valida para avisarle al usuario al instante, sin esperar el viaje de ida y
 * vuelta y sin que pierda lo que escribio.
 *
 * Cada funcion devuelve el mensaje de error, o null si esta todo bien. Asi se
 * pueden encadenar y juntar en un objeto de errores por campo.
 */

// Deliberadamente simple: alcanza con que tenga algo, un arroba, algo, un
// punto y algo. Validar correos "bien" con una expresion regular es un
// problema sin final; el backend usa EmailStr, que hace el trabajo en serio.
const RE_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function validarCorreo(valor) {
  if (!valor.trim()) return 'Escribi tu correo.'
  if (!RE_CORREO.test(valor)) return 'Ese correo no parece valido.'
  return null
}

export function validarClave(valor) {
  if (!valor) return 'Escribi una contrasena.'
  // 8 es el minimo que pide el backend (RegistroIn).
  if (valor.length < 8) return 'Tiene que tener al menos 8 caracteres.'
  // 72 es el tope de bcrypt: mas alla de eso, los caracteres se ignoran.
  if (valor.length > 72) return 'No puede pasar de 72 caracteres.'
  return null
}

export function validarRepetirClave(clave, repetida) {
  if (!repetida) return 'Repeti la contrasena.'
  if (clave !== repetida) return 'Las dos contrasenas no coinciden.'
  return null
}

export function validarTexto(valor, etiqueta, minimo = 1) {
  if (!valor.trim()) return `Completa ${etiqueta}.`
  // La etiqueta viene en minuscula ("tu apellido") para ir en el medio de la
  // frase de arriba; aca abre la oracion, asi que va con mayuscula.
  if (valor.trim().length < minimo) {
    return `${etiqueta.charAt(0).toUpperCase()}${etiqueta.slice(1)} es muy corto.`
  }
  return null
}

/**
 * La fecha de nacimiento define si es menor de edad, y con eso si el perfil de
 * estudiante va a exigir un adulto responsable (ver PUT /perfiles/estudiante/yo).
 */
export function validarFechaNacimiento(valor) {
  if (!valor) return null // es opcional en el registro
  const fecha = new Date(valor)
  if (Number.isNaN(fecha.getTime())) return 'Fecha invalida.'
  if (fecha > new Date()) return 'La fecha no puede ser futura.'
  const anios = (Date.now() - fecha.getTime()) / (365.25 * 24 * 60 * 60 * 1000)
  if (anios > 120) return 'Revisa el ano.'
  return null
}

/** true si a esa fecha de nacimiento le corresponden menos de 18 anios. */
export function esMenorDeEdad(fechaNacimiento) {
  if (!fechaNacimiento) return false
  const fecha = new Date(fechaNacimiento)
  if (Number.isNaN(fecha.getTime())) return false
  const anios = (Date.now() - fecha.getTime()) / (365.25 * 24 * 60 * 60 * 1000)
  // Una fecha futura da edad negativa: no es un menor, es un error de la
  // fecha, y ya lo avisa validarFechaNacimiento().
  return anios >= 0 && anios < 18
}

/**
 * Corre un objeto de validadores contra un objeto de valores.
 * Devuelve { errores, hayErrores }.
 *
 *   const { errores, hayErrores } = validarFormulario({
 *     correo: () => validarCorreo(correo),
 *     clave: () => validarClave(clave),
 *   })
 */
export function validarFormulario(validadores) {
  const errores = {}
  for (const [campo, validar] of Object.entries(validadores)) {
    const error = validar()
    if (error) errores[campo] = error
  }
  return { errores, hayErrores: Object.keys(errores).length > 0 }
}
