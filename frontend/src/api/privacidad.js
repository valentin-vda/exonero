import { pedir } from './cliente.js'

export function obtenerAviso() {
  return pedir('/api/privacidad/aviso', { sinToken: true })
}

export function confirmarConsentimientoParental(datos) {
  return pedir('/api/privacidad/consentimiento-parental', {
    metodo: 'POST', cuerpo: datos, sinToken: true,
  })
}

export async function descargarMisDatos() {
  const token = sessionStorage.getItem('exonero_token')
  const respuesta = await fetch('/api/privacidad/mis-datos', {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  if (!respuesta.ok) throw new Error('No se pudo preparar la exportacion')
  const blob = await respuesta.blob()
  const enlace = document.createElement('a')
  enlace.href = URL.createObjectURL(blob)
  enlace.download = 'exonero-mis-datos.json'
  enlace.click()
  URL.revokeObjectURL(enlace.href)
}

export function anonimizarCuenta(clave) {
  return pedir('/api/privacidad/supresion', {
    metodo: 'POST', cuerpo: { clave, confirmacion: 'ELIMINAR' },
  })
}
