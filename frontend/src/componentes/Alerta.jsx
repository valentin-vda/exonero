/**
 * El cartelito de error o de exito que aparece arriba de los formularios.
 *
 * role="alert" hace que los lectores de pantalla lo lean apenas aparece, sin
 * que el usuario tenga que ir a buscarlo. Es importante en un formulario: si
 * alguien no ve la pantalla, tiene que enterarse de que el login fallo.
 */

export default function Alerta({ tipo = 'error', children }) {
  if (!children) return null

  return (
    <div className={`alerta alerta-${tipo}`} role="alert">
      <span aria-hidden="true">{tipo === 'error' ? '!' : 'OK'}</span>
      <span>{children}</span>
    </div>
  )
}
