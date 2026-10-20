/**
 * El cartelito de error o de exito que aparece arriba de los formularios.
 *
 * role="alert" hace que los lectores de pantalla lo lean apenas aparece, sin
 * que el usuario tenga que ir a buscarlo. Es importante en un formulario: si
 * alguien no ve la pantalla, tiene que enterarse de que el login fallo.
 */

// El simbolito de cada tipo de cartel.
const ICONOS = { error: '!', ok: 'OK', info: 'i' }

export default function Alerta({ tipo = 'error', children }) {
  if (!children) return null

  return (
    // 'info' es un aviso tranquilo, no un error: role="status" lo lee el
    // lector de pantalla sin interrumpir lo que estaba diciendo.
    <div className={`alerta alerta-${tipo}`} role={tipo === 'info' ? 'status' : 'alert'}>
      <span aria-hidden="true">{ICONOS[tipo]}</span>
      <span>{children}</span>
    </div>
  )
}
